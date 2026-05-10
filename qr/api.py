import logging
import os
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, Request, Response, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette import status
from starlette.background import BackgroundTask
from http import HTTPStatus
from io import BytesIO
import json
import base64
import uvicorn
from typing import cast
import uuid

from starlette.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from qr import __version__ as _fallback_version
from qr.schemas import (
    CreateQrRequest,
    QrFormat,
    QrOutput,
    QrErrorCorrection,
)
from qr.generate import generate_qr_image
from qr.log.logger import get_logger
from qr.log.formatter import CustomJSONFormatter

version_prefix = "v1"

try:
    APP_VERSION = _pkg_version("qr-code-api")
except PackageNotFoundError:
    APP_VERSION = _fallback_version

formatter = CustomJSONFormatter("%(asctime)s")
logger = get_logger(__name__, formatter, log_level=logging.INFO)
status_reasons = {x.value: x.name for x in list(HTTPStatus)}

APP_ROOT = Path(os.environ.get("APP_ROOT", "/app"))
if not (APP_ROOT / "site" / "version" / version_prefix).exists():
    APP_ROOT = Path(__file__).resolve().parents[1]

STATIC_FILES_DIR = str(files("qr").joinpath("static"))
DOCS_SITE_DIR = str(APP_ROOT / "site" / "version" / version_prefix)
DOCS_ASSETS_DIR = str(Path(DOCS_SITE_DIR) / "assets")


def get_extra_info(request: Request, request_body, response: Response):
    body = None
    if request_body:
        try:
            body = json.loads(request_body)
        except (json.JSONDecodeError, TypeError):
            body = request_body
    client_host, _ = request.client if request.client else (None, None)
    trace_id = getattr(request.state, "trace_id", "N/A")
    return {
        "trace_id": trace_id,
        "request": {
            "url": request.url.path,
            "method": request.method,
            "http_version": request.scope["http_version"],
            "body": body,
            "query": dict(request.query_params),
            "headers": {
                "host": request.headers.get("host"),
                "user-agent": request.headers.get("user-agent"),
                "accept": request.headers.get("accept"),
            },
            "client_ip": client_host,
            "original_url": str(request.url),
        },
        "response": {
            "status_code": response.status_code,
            "status": status_reasons.get(response.status_code),
        },
    }


async def write_log_data(request, body, response):
    logger.info(
        f"{request.method} {request.url.path}",
        extra={"extra_info": get_extra_info(request, body, response)},
    )


app = FastAPI(
    title="QR Code Generator API",
    description="Generate styled QR codes (classic, rounded, gradient, embedded)",
    version=APP_VERSION,
    docs_url=f"/{version_prefix}/docs",
    redoc_url=f"/{version_prefix}/redoc",
    openapi_url=f"/{version_prefix}/openapi.json",
    openapi_tags=[
        {"name": "QR", "description": "Generate QR codes."},
    ],
)


async def require_json(request: Request):
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be application/json",
        )
    return request


app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")
app.mount(
    f"/{version_prefix}/readme",
    StaticFiles(directory=DOCS_SITE_DIR, html=True),
    name="docs_site",
)
app.mount(
    f"/{version_prefix}/assets",
    StaticFiles(directory=DOCS_ASSETS_DIR),
    name="docs_assets",
)


# Logging middleware
@app.middleware("http")
async def log_request(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id

    req_body = await request.body()
    response = await call_next(request)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    res_body = b"".join(chunks)
    task = BackgroundTask(write_log_data, request, req_body, response)
    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=task,
    )


router = APIRouter(prefix=f"/{version_prefix}")


@app.exception_handler(Exception)
@router.post(
    "/qr",
    summary="Generate QR Code",
    tags=["QR"],
    description="Generate a QR code in PNG, JPEG, WebP, or SVG format. "
    "Supports color masks, embedded images, and optional JSON data URI output.",
    response_description="Returns the QR code as an image or a JSON data URI.",
    dependencies=[Depends(require_json)],
)
async def create_qr(request: CreateQrRequest, raw_request: Request):
    try:
        img = generate_qr_image(
            data=request.data,
            module_drawer=request.module_drawer,
            color_mask=request.color_mask.model_dump() if request.color_mask else None,
            logo=request.logo,
            eye_config_map=request.eye_drawer,
            box_size=request.box_size or 10,
            border=request.border or 4,
            output=request.output or QrOutput(),
            fill_color=request.fill_color,
            back_color=request.back_color,
            version=request.version,
            fit=cast(bool, request.fit if request.fit is not None else True),
            mask_pattern=request.mask_pattern,
            error_correction=cast(
                QrErrorCorrection, request.error_correction or QrErrorCorrection.M
            ),
        )
    except ValueError as e:
        mock_response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(
            f"Value error: {type(e).__name__}: {str(e)}",
            exc_info=True,
            extra={
                "extra_info": get_extra_info(
                    raw_request, request.model_dump(), mock_response
                )
            },
        )

        return JSONResponse({"error": str(e)}, status_code=422)
    except Exception as e:
        mock_response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(
            f"Internal server error: {type(e).__name__}: {str(e)}",
            exc_info=True,
            extra={
                "extra_info": get_extra_info(
                    raw_request, request.model_dump(), mock_response
                )
            },
        )

        return JSONResponse({"error": str(e)}, status_code=500)

    buffer = BytesIO()
    output_format = request.output.format
    as_json = request.output.as_json if hasattr(request, "output") else False

    if output_format == QrFormat.svg:
        img.save(buffer)
        buffer.seek(0)
        mimetype = "image/svg+xml"
    else:
        raster_formats = {
            QrFormat.png: "PNG",
            QrFormat.jpeg: "JPEG",
            QrFormat.webp: "WEBP",
        }
        pil_format = raster_formats.get(output_format, "PNG")
        if pil_format == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buffer, format=pil_format)
        buffer.seek(0)
        mimetype = f"image/{output_format.value.lower()}"

    if as_json:
        data_uri = (
            f"data:{mimetype};base64," + base64.b64encode(buffer.getvalue()).decode()
        )
        return JSONResponse({"data_uri": data_uri})

    return StreamingResponse(buffer, media_type=mimetype)


@app.get("/ping", include_in_schema=False, tags=["Health"])
async def ping():
    return {"status": "ok"}


@app.get("/thumbnail.png", include_in_schema=False)
async def thumbnail():
    return FileResponse(Path(STATIC_FILES_DIR) / "thumbnail.png")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(Path(STATIC_FILES_DIR) / "favicon.ico")


@app.get("/openapi.json", include_in_schema=False)
async def redirect_openapi():
    return RedirectResponse(url=f"/{version_prefix}/openapi.json", status_code=308)


@app.get("/redoc", include_in_schema=False)
async def redirect_redoc():
    return RedirectResponse(url=f"/{version_prefix}/redoc", status_code=308)


app.include_router(router)


# Run server
def run_server(host="0.0.0.0", port=8000, reload=False):
    logger.info(f"Server is listening on http://{host}:{port}")
    uvicorn.run(
        "qr.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        log_config=None,
        access_log=False,
    )
