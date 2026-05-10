import json
import os
from pathlib import Path

import click

from qr.api import run_server
from qr.log.formatter import CustomJSONFormatter
from qr.log.logger import get_logger
from qr.generate import generate_qr_image
from qr.schemas import CreateQrRequest
from pydantic import ValidationError

formatter = CustomJSONFormatter("%(asctime)s")
logger = get_logger(__name__, formatter)


@click.group(help="QR Code Generator CLI")
def cli():
    pass


@cli.command(help="Generate a QR code from JSON (string or file).")
@click.argument("json_input")
def generate(json_input):
    """
    JSON string or JSON file path matching CreateQrRequest fields, e.g.:

    qr generate '{"data":"Hello World","box_size":10,"border":4}'
    """
    try:
        if os.path.isfile(json_input):
            with open(json_input, "r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = json.loads(json_input)

        request = CreateQrRequest(**payload)  # Pydantic validation
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Invalid JSON or file error: {e}")
        return
    except ValidationError as e:
        logger.error(f"Schema validation error: {e}")
        return

    img = generate_qr_image(
        data=request.data,
        module_drawer=request.module_drawer,
        color_mask=request.color_mask.model_dump() if request.color_mask else None,
        logo=request.logo,
        eye_config_map=request.eye_drawer,
        box_size=request.box_size,
        border=request.border,
        output=request.output,
        fill_color=request.fill_color,
        back_color=request.back_color,
        version=request.version,
        fit=request.fit,
        mask_pattern=request.mask_pattern,
        error_correction=request.error_correction,
    )

    output_directory = Path("./output")
    output_file = (
        output_directory / f"output.{request.output.format.value}"
    ).absolute()
    img.save(output_file)
    logger.info(f"Saved QR code to {output_file}")


@cli.command(help="Run the FastAPI server.")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True)
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def server(host, port, reload):
    run_server(host, port, reload)
