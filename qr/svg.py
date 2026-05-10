from decimal import Decimal
from typing import Dict, Type, Any, Tuple

import qrcode.image.base
from qrcode.compat.etree import ET  # type: ignore[import]
from qrcode.image import svg
from qrcode.image.styles.moduledrawers import svg as svg_drawers

from qr.schemas import QrModuleDrawer, SvgBaseModuleDrawerOptions, BackgroundCSS


class SvgCustomImage(svg.SvgFragmentImage):
    drawer_aliases: qrcode.image.base.DrawerAliases = {}
    background_css_string: str = "fill: #FFFFFF; fill-opacity: 1.0;"

    def _svg(self, tag="svg", **kwargs):
        svg = super()._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        if self.background_css_string:
            svg.append(
                ET.Element(
                    "rect",
                    x="0",
                    y="0",
                    width="100%",
                    height="100%",
                    attrib={
                        "style": self.background_css_string,
                    },
                )
            )
        return svg

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=True)


class SvgPathImageCustom(svg.SvgPathImage):
    drawer_aliases: qrcode.image.base.DrawerAliases = {}
    background_css_string: str = "fill: #FFFFFF; fill-opacity: 1.0;"

    # We do not need to copy drawer aliases since we manage drawer selection via schema

    def __init__(self, *args, **kwargs):
        self._subpaths: list[str] = []  # type: ignore[annotation-unchecked]
        super().__init__(*args, **kwargs)

    def drawrect(self, row: int, col: int):
        box = self.pixel_box(row, col)
        # Use the module drawer to generate the path for the module
        path_str = self.module_drawer.path(box)  # type: ignore[attr-defined]
        # Store the path
        self._subpaths.append(path_str)

    def process(self):
        # Store the path just in case someone wants to use it again or in some
        # unique way.
        self.path = ET.Element(
            ET.QName("path"),  # type: ignore[call-arg]
            d="".join(self._subpaths),
            id="qr-path",
            attrib={
                "style": self.background_css_string,
            },
        )
        self._subpaths = []
        self._img.append(self.path)


def dict_to_css_string(css_dict: BackgroundCSS) -> str:
    # Ensure all values are cast to string for the style attribute
    return "; ".join(f"{k}: {v}" for k, v in css_dict.items()) + ";"


def create_dynamic_svg_image_class(
    drawer_options: SvgBaseModuleDrawerOptions,
) -> Type[SvgCustomImage]:
    ratio = drawer_options.ratio
    if ratio is None:
        ratio = 0.8
    css_style = dict_to_css_string(drawer_options.style.background)
    drawer_type_name = getattr(drawer_options.type, "value", drawer_options.type)

    # 3. MAP DRAWER TYPE TO BASE CLASS (for drawer_aliases)
    # FIX: Use Type[Any] to simplify the type hint and avoid dependency issues.
    drawer_class_map: Dict[str, Type[Any]] = {
        QrModuleDrawer.SvgSquareDrawer.value: svg_drawers.SvgSquareDrawer,
        QrModuleDrawer.SvgCircleDrawer.value: svg_drawers.SvgCircleDrawer,
        QrModuleDrawer.SvgPathSquareDrawer.value: svg_drawers.SvgPathSquareDrawer,
        QrModuleDrawer.SvgPathCircleDrawer.value: svg_drawers.SvgPathCircleDrawer,
    }

    path_drawers = {
        QrModuleDrawer.SvgPathSquareDrawer.value,
        QrModuleDrawer.SvgPathCircleDrawer.value,
    }

    drawer_type_class = drawer_class_map.get(drawer_options.type)
    if not drawer_type_class:
        raise ValueError(f"Unknown SVG drawer type: {drawer_options.type}")

    base_image_class: Type[SvgCustomImage | SvgPathImageCustom]
    if drawer_type_name in path_drawers:
        base_image_class = SvgPathImageCustom
    else:
        base_image_class = SvgCustomImage

    dynamic_alias: Tuple[Type[Any], Dict[str, Any]] = (
        drawer_type_class,
        {"size_ratio": Decimal(ratio)},
    )

    new_aliases = {
        drawer_options.type: dynamic_alias,
    }

    # 6. DYNAMICALLY CREATE THE SUBCLASS
    class_name = (
        f"DynamicSvgImage_{drawer_type_name.replace('-', '_')}_{int(ratio * 100)}"
    )

    DynamicSvgImageClass = type(
        class_name,
        (base_image_class,),
        {
            "drawer_aliases": new_aliases,
            "background_css_string": css_style,  # Pass the single CSS string
        },
    )
    return DynamicSvgImageClass
