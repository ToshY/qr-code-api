<h1 align="center">𝄃𝄃𝄂𝄂𝄀𝄁𝄃𝄂𝄂𝄃 qr-code-api </h1>

<div align="center">
    <img src="https://img.shields.io/github/v/release/toshy/qr-code-api?label=Release&sort=semver" alt="Current release version" />
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/codestyle.yml?branch=main&label=Black" alt="Black">
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/codequality.yml?branch=main&label=Ruff" alt="Ruff">
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/statictyping.yml?branch=main&label=Mypy" alt="Mypy">
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/test.yml?branch=main&label=Pytest" alt="Pytest">
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/security.yml?branch=main&label=Security%20check" alt="Security check" />
    <img src="https://img.shields.io/github/actions/workflow/status/toshy/qr-code-api/build.yml?branch=main&label=Docker%20build" alt="Docker build" />
    <br /><br />
    <div>A command-line utility and API for creating QR codes.</div>
</div>

## 📝 Quickstart

The published image is available at [`ghcr.io/toshy/qr-code-api`](ghcr.io/toshy/qr-code-api).

By default, the container runs in **CLI mode**; pass `server` as the argument to instead start the **FastAPI server**.

### ⚙ CLI

Make sure you have a writable `./output/` directory (same user) for the CLI to write generated QR code images into.

```shell
mkdir -p ./output
```

#### `docker run`

Show CLI help (default):

```sh
docker run --rm ghcr.io/toshy/qr-code-api:latest
```

Generate a QR code into `./output/`:

```sh
docker run --rm \
  -u $(id -u):$(id -g) \
  -v ${PWD}/output:/app/output \
  ghcr.io/toshy/qr-code-api:latest \
  generate '{"data":"https://example.com"}'
```

#### `docker compose`

Add a one-shot CLI service to your `compose.yaml`:

```yaml
services:
  qr-code-cli:
    image: ghcr.io/toshy/qr-code-api:latest
    user: "${UID:-1000}:${GID:-1000}"
    volumes:
      - ./output:/app/output
```

Run it with the desired CLI args (these are appended to the image's `ENTRYPOINT` and override the default `--help`):

```sh
docker compose run --rm qr-code-cli generate '{"data":"https://example.com"}'
```

### 🚀 API server

The server listens on port `8000`. For each major API version `v{N}` (e.g. `v1`), the following endpoints are exposed:

| Endpoint             | Method | Description                                                              |
|----------------------|--------|--------------------------------------------------------------------------|
| `/v{N}/qr`           | `POST` | Generate a QR code (PNG, JPEG, WebP, or SVG; raw image or JSON data URI) |
| `/v{N}/docs`         | `GET`  | Swagger UI                                                               |
| `/v{N}/redoc`        | `GET`  | ReDoc                                                                    |
| `/v{N}/readme`       | `GET`  | Rendered README documentation                                            |
| `/v{N}/openapi.json` | `GET`  | OpenAPI specification                                                    |

#### `docker run`

```sh
docker run --rm \
  -u $(id -u):$(id -g) \
  -p 8000:8000 \
  ghcr.io/toshy/qr-code-api:latest \
  server
```

Then open <http://localhost:8000/v1/docs>.

Test the endpoint:

```sh
curl -X POST http://localhost:8000/v1/qr \
  -H 'Content-Type: application/json' \
  -d '{"data":"https://example.com"}' \
  --output qr.png
```

#### `docker compose`

```yaml
services:
  qr-code-api:
    image: ghcr.io/toshy/qr-code-api:latest
    user: "${UID:-1000}:${GID:-1000}"
    ports:
      - "8000:8000"
    command: ["server"]
    restart: unless-stopped
```

```sh
docker compose up -d qr-code-api
```

#### 🔐 Authentication (optional)

The `POST /v{N}/qr` endpoint can be protected by a shared API key. Authentication is **disabled by default** and activates only when the `QR_CODE_API_KEYS` environment variable is set to a non-empty, comma-separated list of valid keys.

Keys are sent as a Bearer token in the `Authorization` header:

```
Authorization: Bearer <your-api-key>
```

The Swagger UI at `/v{N}/docs` exposes an **Authorize** button so you can paste a key once and use "Try it out" interactively. The remaining endpoints (`/docs`, `/redoc`, `/readme`, `/openapi.json`) stay public so the docs are always reachable.

##### With `docker run`

```sh
export QR_CODE_API_KEYS="$(openssl rand -hex 32)"

docker run --rm \
  -u $(id -u):$(id -g) \
  -p 8000:8000 \
  -e QR_CODE_API_KEYS \
  ghcr.io/toshy/qr-code-api:latest \
  server
```

##### With `docker compose`

Add the env var to the service. Reading it from the host shell (or a `.env` file next to `compose.yaml`) keeps the secret out of version control:

```yaml
services:
  qr-code-api:
    image: ghcr.io/toshy/qr-code-api:latest
    user: "${UID:-1000}:${GID:-1000}"
    ports:
      - "8000:8000"
    environment:
      QR_CODE_API_KEYS: ${QR_CODE_API_KEYS:?set QR_CODE_API_KEYS in your .env or shell}
    command: ["server"]
    restart: unless-stopped
```

`.env` (gitignored):

```dotenv
QR_CODE_API_KEYS=replace-with-a-long-random-string,optional-second-key
```

```sh
docker compose up -d qr-code-api
```

##### Calling a protected endpoint

```sh
curl -X POST http://localhost:8000/v1/qr \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${QR_CODE_API_KEYS%%,*}" \
  -d '{"data":"https://example.com"}' \
  --output qr.png
```

> The `${QR_CODE_API_KEYS%%,*}` expansion sends only the first key when multiple are configured.

## 🛠️ Contribute

### Requirements

* ☑️ [Pre-commit](https://pre-commit.com/#installation).
* 🐋 [Docker Compose V2](https://docs.docker.com/compose/install/)
* 📋 [Task 3.37+](https://taskfile.dev/installation/)

### Tools

- URL-encoder for SVG: https://yoksel.github.io/url-encoder/
- PNG to base64: https://www.base64-image.de/

## ℹ️ Information

- https://github.com/lincolnloop/python-qrcode
- https://github.com/reegan-anne/python_qrcode/blob/main/main.ipynb
- https://medium.com/@kamilmatejuk/how-to-easily-create-custom-qr-codes-in-python-e0f5ca6364a1
- https://github.com/KamilMatejuk/python-qrcode

## ❕ License

This repository comes with a [BSD 3-Clause License](./LICENSE).
