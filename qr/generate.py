from typing import Any, Dict, Tuple, Union, Type, Callable
from typing import cast

import qrcode
import qrcode.image.base
from PIL import Image
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_M,
    ERROR_CORRECT_L,
    ERROR_CORRECT_Q,
)
from qrcode.image.pil import PilImage
from qrcode.image.styledpil import StyledPilImage

from qr.helper import decode_base64_to_image, to_rgb_tuple
from qr.log.formatter import CustomJSONFormatter
from qr.log.logger import get_logger
from qr.mask import create_color_mask
from qr.pil import (
    StyledPilImageEyeDrawer,
    ConfigurableEyeDrawer,
    create_pil_drawer_instance_factory,
)
from qr.schemas import (
    QrColorMaskType,
    QrModuleDrawer,
    QrErrorCorrection,
    QrOutput,
    QrEyePosition,
    QrEyeConfiguration,
    SquareModuleDrawerOptions,
    BaseModuleDrawerOptions,
    SvgBaseModuleDrawerOptions,
    QrLogoConfiguration,
    RGBColor,
)
from qr.svg import create_dynamic_svg_image_class

formatter = CustomJSONFormatter("%(asctime)s")
logger = get_logger(__name__, formatter)

ERROR_MAP = {
    QrErrorCorrection.L: ERROR_CORRECT_L,
    QrErrorCorrection.M: ERROR_CORRECT_M,
    QrErrorCorrection.Q: ERROR_CORRECT_Q,
    QrErrorCorrection.H: ERROR_CORRECT_H,
}

MODULE_DRAWERS: Dict[str, Tuple[Union[Type, Callable], Union[Any, None]]] = {
    # SVG Drawers
    QrModuleDrawer.SvgSquareDrawer.value: (create_dynamic_svg_image_class, None),
    QrModuleDrawer.SvgCircleDrawer.value: (create_dynamic_svg_image_class, None),
    QrModuleDrawer.SvgPathSquareDrawer.value: (create_dynamic_svg_image_class, None),
    QrModuleDrawer.SvgPathCircleDrawer.value: (create_dynamic_svg_image_class, None),
    # PIL Drawers
    QrModuleDrawer.SquareModuleDrawer.value: (create_pil_drawer_instance_factory, None),
    QrModuleDrawer.GappedSquareModuleDrawer.value: (
        create_pil_drawer_instance_factory,
        None,
    ),
    QrModuleDrawer.CircleModuleDrawer.value: (create_pil_drawer_instance_factory, None),
    QrModuleDrawer.RoundedModuleDrawer.value: (
        create_pil_drawer_instance_factory,
        None,
    ),
    QrModuleDrawer.VerticalBarsDrawer.value: (
        create_pil_drawer_instance_factory,
        None,
    ),
    QrModuleDrawer.HorizontalBarsDrawer.value: (
        create_pil_drawer_instance_factory,
        None,
    ),
}


# https://github.com/lincolnloop/python-qrcode
# https://github.com/reegan-anne/python_qrcode/blob/main/main.ipynb
# https://medium.com/@kamilmatejuk/how-to-easily-create-custom-qr-codes-in-python-e0f5ca6364a1
# https://github.com/KamilMatejuk/python-qrcode
def generate_qr_image(
    data: str,
    module_drawer: BaseModuleDrawerOptions = SquareModuleDrawerOptions(),
    color_mask: dict[str, Any] | None = None,
    logo: QrLogoConfiguration | None = None,
    eye_config_map: Dict[QrEyePosition, QrEyeConfiguration] | None = None,
    box_size: int = 10,
    border: int = 4,
    output: QrOutput = QrOutput(),
    fill_color: RGBColor = RGBColor(r=0, g=0, b=0),
    back_color: RGBColor = RGBColor(r=255, g=255, b=255),
    version: int | None = 3,
    fit: bool = True,
    mask_pattern: int | None = None,
    error_correction: QrErrorCorrection = QrErrorCorrection.M,
):
    """Generate a QR code with full drawer, color mask, and optional embedded image support."""
    actual_fit = True if version is None else fit

    qr = qrcode.QRCode(
        version=version,
        error_correction=ERROR_MAP[error_correction],
        box_size=box_size,
        border=border,
        mask_pattern=mask_pattern,
    )
    qr.add_data(data)
    qr.make(fit=actual_fit)

    drawer_type_name = module_drawer.type

    if drawer_type_name not in MODULE_DRAWERS:
        raise ValueError(
            f"Unsupported module drawer type: '{drawer_type_name}'. "
            f"Available types: {list(MODULE_DRAWERS.keys())}"
        )

    factory_or_func, drawer_instance = MODULE_DRAWERS[drawer_type_name]

    factory: Type[qrcode.image.base.BaseImage] = StyledPilImage
    module_drawer_arg: Any = None
    svg_kwargs = {}
    dynamic_result = factory_or_func(module_drawer)
    if factory_or_func is create_dynamic_svg_image_class:
        # SVG path: factory_or_func returns the Image Class
        factory = dynamic_result
        module_drawer_arg = getattr(module_drawer.type, "value", module_drawer.type)
        if isinstance(module_drawer, SvgBaseModuleDrawerOptions):
            raw_svg_kwargs = module_drawer.style.svg
        else:
            raw_svg_kwargs = {}

        svg_kwargs = {k: str(v) for k, v in raw_svg_kwargs.items()}
    elif factory_or_func is create_pil_drawer_instance_factory:
        # PIL path: factory_or_func returns the Drawer Instance
        module_drawer_arg = dynamic_result
        svg_kwargs = {}
    else:
        raise ValueError("Unknown dynamic factory function encountered.")

    kwargs: dict[str, Any] = {**{"module_drawer": module_drawer_arg}, **svg_kwargs}

    # --- Color mask ---
    col_mask_instance = None
    if color_mask:
        mask_type = color_mask.get("type")
        options = color_mask.get("options", {})
        if mask_type is None:
            raise ValueError("Color mask type must be provided")
        col_mask_instance = create_color_mask(cast(QrColorMaskType, mask_type), options)

    output_format = output.format
    # --- SVG output ---
    if output_format == "svg":
        kwargs = {**kwargs, **svg_kwargs}
        return qr.make_image(image_factory=factory, **kwargs)

    # --- PNG output ---
    if output_format == "png" or output_format == "jpeg" or output_format == "webp":
        if col_mask_instance:
            kwargs["color_mask"] = col_mask_instance

        if eye_config_map:
            factory = StyledPilImageEyeDrawer
            kwargs["eye_drawer"] = ConfigurableEyeDrawer(eye_config_map=eye_config_map)  # type: ignore[arg-type]

        if back_color is not None:
            kwargs["back_color"] = to_rgb_tuple(back_color)
        if fill_color is not None:
            kwargs["fill_color"] = to_rgb_tuple(fill_color)

        if (
            (back_color is not None or fill_color is not None)
            and col_mask_instance is None
            and not eye_config_map
        ):
            factory = PilImage

        # Embedded image / logo support
        if logo:
            try:
                kwargs["embedded_image"] = decode_base64_to_image(logo.image)
            except Exception as e:
                raise ValueError(f"Invalid logo image: {e}")

            if logo.ratio:
                kwargs["embedded_image_ratio"] = logo.ratio

            if logo.filter:
                kwargs["embedded_image_resample"] = Image.Resampling[logo.filter.name]

        return qr.make_image(image_factory=factory, **kwargs)

    raise ValueError(f"Unsupported combination: {module_drawer} + {output_format}")
