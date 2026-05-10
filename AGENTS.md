# AGENTS.md

Guidance for AI coding agents working in this repository.

## General Rules

- Respect `.gitignore` and `.aiignore` files in the repo.
- Respect existing AI conventions documented in the repo — read and follow `CLAUDE.md` (behavioral guidelines: think before coding, simplicity first, surgical changes, goal-driven execution) in addition to this file

## Architecture

Single Python package `qr/` exposing the **same QR generation core** through two entry points:

- **CLI** (`qr/cli.py`, `qr/__main__.py`): `python -m qr generate '<json>'` and `python -m qr server`. Uses Click; the `generate` command parses a JSON string OR a file path, validates via the same Pydantic `CreateQrRequest` used by the API, and writes to `./output/output.<format>`.
- **HTTP API** (`qr/api.py`): FastAPI app, single business endpoint `POST /v1/qr`. Versioned prefix `v1` is hardcoded (`version_prefix`). Mounts the Zensical-built docs site at `/v1/readme` (built into `/app/site` by `task zensical:build`).

Both paths converge on `qr.generate.generate_qr_image(...)`, which dispatches via the `MODULE_DRAWERS` dict (`qr/generate.py`) to either:
- **SVG path** → `create_dynamic_svg_image_class` (`qr/svg.py`) returning an image *class* (factory).
- **PIL path** → `create_pil_drawer_instance_factory` (`qr/pil.py`) returning a drawer *instance*. Eye customization swaps factory to `StyledPilImageEyeDrawer` + `ConfigurableEyeDrawer`. Color masks come from `qr/mask.py`.

The discriminator pattern is central: `CreateQrRequest.module_drawer` is a `Union[...]` discriminated by `type` (the `QrModuleDrawer` enum value, e.g. `"svg_circle"`, `"rounded_module"`). Mismatches between drawer family and `output.format` are rejected by `validate_module_drawer_for_format` (SVG drawer + PNG output → 422). Logos require `error_correction == "H"` (`validate_logo_error_correction`).

## Conventions

- **Schemas** (`qr/schemas.py`) are the source of truth for validation, OpenAPI examples, and CLI input. When adding a drawer/mask/option, add an enum value, a `*Options` Pydantic class with `type: Literal[QrModuleDrawer.X] = QrModuleDrawer.X`, register it in `MODULE_DRAWERS`, and add it to the `Union` in `CreateQrRequest.module_drawer`.
- **Colors**: always `RGBColor` (Pydantic) externally; convert via `qr.helper.to_rgb_tuple` before passing to `python-qrcode`.
- **Logging**: use `qr.log.logger.get_logger(__name__, CustomJSONFormatter("%(asctime)s"))`. The API middleware injects `request.state.trace_id` (uuid4) and logs structured JSON via `extra={"extra_info": get_extra_info(...)}` as a `BackgroundTask` after the response.
- **Errors in API**: `ValueError` → 422 JSON `{"error": ...}`; other exceptions → 500. Don't raise `HTTPException` for validation; let Pydantic do it (returns 422 automatically).
- **Content-Type guard**: `POST /v1/qr` requires `application/json` (enforced by `require_json` dependency → 415).

## Developer Workflows

All commands run through Docker via `Taskfile.yml` — do NOT assume a local venv.

- `task up` / `task down` — run dev server at http://localhost:8000/v1/docs (compose mounts `./` into `/app` with `--reload`).
- `task dev:cli -- '{"data":"hi"}'` — exercise CLI in dev container; output written to `./output/`.
- `task pytest` — runs `pytest --snapshot-update` (uses **syrupy**; snapshots in `tests/__snapshots__/test_api.ambr`). Tests hit FastAPI via `TestClient`; binary QR output is snapshot-compared byte-for-byte, so regenerating drawers will require updating snapshots.
- `task contribute` — runs `black:fix`, `ruff:fix`, `mypy`, `pytest` (the pre-merge gate).
- `task openapi` — requires `task up` first; curls `/v1/openapi.json` into `docs/version/v1/openapi.json` (committed; `scripts/check-version-docs.sh` validates this in CI).
- `task zensical:build` / `task zensical:live` — builds versioned docs site needed by `/v1/readme` mount. Uses [Zensical](https://zensical.org) (`zensical/zensical` Docker image, config in `zensical.toml`). The Taskfile runs `envsubst` on `zensical.toml` to expand `$MAJOR_VERSION` (auto-detected as the highest `v*` dir under `docs/version/`) into a temp `.zensical.runtime.toml` before invoking `zensical build` / `zensical serve -f ...`.

## Integration Notes

- `APP_ROOT` env var (default `/app`) locates the built docs at `site/version/v1`; falls back to repo root for source checkouts.
- App version resolved via `importlib.metadata.version("qr-code-api")`, falling back to `qr.__version__`.
- Static assets (`favicon.ico`, `thumbnail.png`) shipped inside the package via `importlib.resources.files("qr").joinpath("static")`.

## Releasing

The version is defined in **one place**: `qr/__init__.py` (`__version__ = "X.Y.Z"`).

`setup.py` parses it via regex; `qr/api.py` reads it through `importlib.metadata` (with `qr.__version__` as a fallback), so the value flows automatically into the installed package metadata, the FastAPI `/v1/openapi.json` `info.version` field, and anywhere else the version is consumed.

**Before creating a new git tag, you MUST bump `qr/__init__.py` to match the tag you intend to push.** The git tag and `__version__` are expected to be identical (e.g. tag `1.2.4` ↔ `__version__ = "1.2.4"`). The `build.yml` workflow does not auto-derive the version from git, so a mismatch will publish a Docker image whose internal version disagrees with its tag.

Recommended release flow:

1. Edit `qr/__init__.py` → set `__version__ = "X.Y.Z"`.
2. Commit (`chore: bump version to X.Y.Z`).
3. Tag: `git tag X.Y.Z && git push origin main --tags`.
4. The `Build and Push Docker image` workflow handles the rest (publishes `:X.Y.Z`, `:X.Y`, `:X`, and — if it's the highest stable tag — `:latest`).

Quick sanity check after bumping (run from the dev container):

```bash
task shell:dev -- python3 -c "from qr import __version__; print(__version__)"
```




