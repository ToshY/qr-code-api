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

The published image is `ghcr.io/toshy/qr-code-api`. By default, the container runs in **CLI mode** (the `ENTRYPOINT` is the `qr` command, with `--help` as the default `CMD`); pass `server` as the argument to instead start the **FastAPI server**.

### CLI

#### `docker run`

Show CLI help (default):

```sh
docker run --rm ghcr.io/toshy/qr-code-api:latest
```

Generate a QR code into `./output/`:

```sh
mkdir -p output
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

### API server

The server listens on port `8000` and exposes Swagger UI at `/v1/docs`.

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
