from typing import Any
from typing import cast

from pydantic import BaseModel
from qrcode.image.styles.colormasks import (
    SolidFillColorMask,
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask,
    ImageColorMask,
)

from qr.helper import decode_base64_to_image, to_rgb_tuple
from qr.schemas import (
    QrColorMaskType,
    SolidFillOptions,
    SquareGradientOptions,
    HorizontalGradientOptions,
    VerticalGradientOptions,
    ImageMaskOptions,
    RadialGradientOptions,
    RGBColor,
)

COLOR_MASK_MAP = {
    QrColorMaskType.SolidFill: SolidFillColorMask,
    QrColorMaskType.RadialGradient: RadialGradiantColorMask,
    QrColorMaskType.SquareGradient: SquareGradiantColorMask,
    QrColorMaskType.HorizontalGradient: HorizontalGradiantColorMask,
    QrColorMaskType.VerticalGradient: VerticalGradiantColorMask,
    QrColorMaskType.Image: ImageColorMask,
}


def create_color_mask(
    mask_type: QrColorMaskType, options: dict[str, Any] | None = None
):
    """Create a color mask instance from the type and options dict, using schema defaults if not provided."""
    options_model = cast(
        type[BaseModel] | None,
        {
            QrColorMaskType.SolidFill: SolidFillOptions,
            QrColorMaskType.RadialGradient: RadialGradientOptions,
            QrColorMaskType.SquareGradient: SquareGradientOptions,
            QrColorMaskType.HorizontalGradient: HorizontalGradientOptions,
            QrColorMaskType.VerticalGradient: VerticalGradientOptions,
            QrColorMaskType.Image: ImageMaskOptions,
        }.get(mask_type),
    )

    if not options_model:
        raise ValueError(f"Unsupported color mask type: {mask_type}")

    validated: BaseModel = options_model(**(options or {}))

    kwargs = {}
    for field_name, field_value in validated.__dict__.items():
        if isinstance(field_value, RGBColor):
            kwargs[field_name] = to_rgb_tuple(field_value)
        elif isinstance(field_value, str) and field_name == "color_mask_image":
            kwargs[field_name] = decode_base64_to_image(field_value)  # type: ignore[assignment]
        else:
            kwargs[field_name] = field_value

    mask_class = COLOR_MASK_MAP[mask_type]

    return mask_class(**kwargs)
