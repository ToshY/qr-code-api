import base64
import io
from typing import Any

from PIL import Image

from qr.schemas import (
    RGBColor,
)


def decode_base64_to_image(b64_string: str) -> Image.Image:
    """Decode a base64-encoded string to a Pillow Image."""
    try:
        image_bytes = base64.b64decode(b64_string)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        return image
    except Exception as e:
        raise ValueError(f"Invalid base64 image: {e}")


def to_rgb_tuple(color: RGBColor | tuple[int, int, int]) -> tuple[int, int, int]:
    """Convert RGBAColor or tuple to (r,g,b)."""
    if isinstance(color, RGBColor):
        return color.r, color.g, color.b
    elif isinstance(color, tuple):
        return color
    else:
        raise ValueError(f"Invalid color: {color}")


def parse_rgb(color: Any) -> tuple[int, int, int]:
    """Convert dict or list to (r,g,b) tuple, validating range 0–255."""
    if isinstance(color, dict):
        try:
            r = int(color["r"])
            g = int(color["g"])
            b = int(color["b"])
        except KeyError as e:
            raise ValueError(f"Missing key in color dict: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid color value in dict: {e}")
    elif isinstance(color, (list, tuple)) and len(color) == 3:
        try:
            r, g, b = (int(color[0]), int(color[1]), int(color[2]))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid color values in list/tuple: {e}")
    else:
        raise ValueError(f"Invalid color format: {color}")

    for c in (r, g, b):
        if not (0 <= c <= 255):
            raise ValueError(
                f"Color values must be integers between 0 and 255: {color}"
            )

    return r, g, b
