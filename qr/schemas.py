from pydantic import BaseModel, conint, model_validator, Field, ConfigDict
from typing import Optional, Union, Annotated, List, Dict, Literal
from enum import Enum

RGBInt = Annotated[int, conint(ge=0, le=255)]


class RGBColor(BaseModel):
    r: Annotated[RGBInt, Field(description="Red channel (0–255)", json_schema_extra={"example": 255})] = 255  # type: ignore[call-arg]
    g: Annotated[RGBInt, Field(description="Green channel (0–255)", json_schema_extra={"example": 255})] = 255  # type: ignore[call-arg]
    b: Annotated[RGBInt, Field(description="Blue channel (0–255)", json_schema_extra={"example": 255})] = 255  # type: ignore[call-arg]


class QrEyeDrawerStyle(BaseModel):
    outline: Annotated[Union[RGBColor, str], Field(description="Outline color (accepts RGB object or color string like 'black').")] = RGBColor(r=0, g=0, b=0)  # type: ignore[call-arg]
    radius: Annotated[float, Field(description="Normalized radius factor (0.0=square, 1.0=max curve).", ge=0.0, le=1.0, json_schema_extra={"example": 0.8})] = 0.0  # type: ignore[call-arg]
    corners: Annotated[List[bool], Field(description="List of 4 booleans [NW, NE, SE, SW] to enable rounding on each corner.", min_length=4, max_length=4, json_schema_extra={"example": [True, True, False, True]})] = [True, True, True, True]  # type: ignore[call-arg]


class QrEyeConfiguration(BaseModel):
    outer: Annotated[QrEyeDrawerStyle, Field(description="Styling for the 7x7 outer eye frame.")] = QrEyeDrawerStyle(fill=False, radius=0.0)  # type: ignore[call-arg]
    inner: Annotated[QrEyeDrawerStyle, Field(description="Styling for the 3x3 inner eyeball.")] = QrEyeDrawerStyle(fill=True, radius=0.0)  # type: ignore[call-arg]


class QrEyePosition(str, Enum):
    top_left = "top_left"
    top_right = "top_right"
    bottom_left = "bottom_left"


class QrModuleDrawer(str, Enum):
    SvgSquareDrawer = "svg_square"
    SvgCircleDrawer = "svg_circle"
    SvgPathSquareDrawer = "svg_path_square"
    SvgPathCircleDrawer = "svg_path_circle"
    SquareModuleDrawer = "square_module"
    GappedSquareModuleDrawer = "gapped_square_module"
    CircleModuleDrawer = "circle_module"
    RoundedModuleDrawer = "rounded_module"
    VerticalBarsDrawer = "vertical_bars"
    HorizontalBarsDrawer = "horizontal_bars"


SVGStyleValue = Union[str, float, int]
BackgroundCSSValue = Union[str, float, int]
BackgroundCSS = Dict[str, BackgroundCSSValue]
SVGStyleOptions = Dict[str, SVGStyleValue]  # For kwargs like 'scale', 'unit', etc.


class StyleOptions(BaseModel):
    # SVG properties passed as kwargs to qr.make_image (e.g., 'unit')
    svg: Annotated[
        SVGStyleOptions,
        Field(
            description="Keyword arguments passed directly to the SVG image factory (e.g., 'unit', 'scale'). Only used for SVG output.",
            json_schema_extra={"example": {"unit": "mm"}},
        ),
    ] = Field(
        default_factory=dict
    )  # type: ignore
    # CSS properties used to style the background rect inside the factory
    background: Annotated[
        BackgroundCSS,
        Field(
            description="Arbitrary CSS key-value pairs for the QR background rectangle. Only used for SVG output.",
            json_schema_extra={"example": {"fill": "#FFFFFF", "fill-opacity": 1.0}},
        ),
    ] = {
        "fill": "#FFFFFF",
        "fill-opacity": 1.0,
    }  # type: ignore[call-arg]


# Base model to act as a discriminator in the Union
class BaseModuleDrawerOptions(BaseModel):
    type: str = Field(..., frozen=True, description="The type of the module drawer.")
    model_config = ConfigDict(extra="forbid")


class SvgBaseModuleDrawerOptions(BaseModuleDrawerOptions):
    ratio: Annotated[
        float,
        Field(
            description="The ratio of the module size to the box size (0.0 to 1.0). Controls the gap between modules.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8
    style: StyleOptions = Field(default_factory=StyleOptions)


class PilBaseModuleDrawerOptions(BaseModuleDrawerOptions):
    pass


class SvgSquareDrawerOptions(SvgBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.SvgSquareDrawer] = QrModuleDrawer.SvgSquareDrawer


class SvgPathSquareDrawerOptions(SvgBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.SvgPathSquareDrawer] = (
        QrModuleDrawer.SvgPathSquareDrawer
    )


class SvgCircleDrawerOptions(SvgBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.SvgCircleDrawer] = QrModuleDrawer.SvgCircleDrawer


class SvgPathCircleDrawerOptions(SvgBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.SvgPathCircleDrawer] = (
        QrModuleDrawer.SvgPathCircleDrawer
    )


class SquareModuleDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.SquareModuleDrawer] = QrModuleDrawer.SquareModuleDrawer


class VerticalBarsDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.VerticalBarsDrawer] = QrModuleDrawer.VerticalBarsDrawer
    shrink: Annotated[
        float,
        Field(
            description="The horizontal shrink ratio. Controls the thickness of the bars. Smaller value equals smaller bars.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8


class HorizontalBarsDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.HorizontalBarsDrawer] = (
        QrModuleDrawer.HorizontalBarsDrawer
    )
    shrink: Annotated[
        float,
        Field(
            description="The vertical shrink ratio. Controls the thickness of the bars. Smaller value equals smaller bars.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8


class GappedSquareModuleDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.GappedSquareModuleDrawer] = (
        QrModuleDrawer.GappedSquareModuleDrawer
    )
    ratio: Annotated[
        float,
        Field(
            description="The ratio of the module size to the box size (0.0 to 1.0). Controls the gap between modules.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8


class CircleModuleDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.CircleModuleDrawer] = QrModuleDrawer.CircleModuleDrawer
    ratio: Annotated[
        float,
        Field(
            description="The ratio of the module size to the box size (0.0 to 1.0). Controls the gap between modules.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8


class RoundedModuleDrawerOptions(PilBaseModuleDrawerOptions):
    type: Literal[QrModuleDrawer.RoundedModuleDrawer] = (
        QrModuleDrawer.RoundedModuleDrawer
    )
    ratio: Annotated[
        float,
        Field(
            description="The ratio of the module size to the box size (0.0 to 1.0). Controls the gap between modules.",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.8},
        ),
    ] = 0.8


class QrColorMaskType(str, Enum):
    SolidFill = "solid"
    RadialGradient = "radial"
    SquareGradient = "square"
    HorizontalGradient = "horizontal"
    VerticalGradient = "vertical"
    Image = "image"


class SolidFillOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    front_color: Annotated[RGBColor, Field(description="Foreground color")] = RGBColor(
        r=0, g=0, b=0
    )


class RadialGradientOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    center_color: Annotated[RGBColor, Field(description="Center color")] = RGBColor(
        r=0, g=0, b=0
    )
    edge_color: Annotated[RGBColor, Field(description="Edge color")] = RGBColor(
        r=0, g=0, b=255
    )


class SquareGradientOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    center_color: Annotated[RGBColor, Field(description="Center color")] = RGBColor(
        r=0, g=0, b=0
    )
    edge_color: Annotated[RGBColor, Field(description="Edge color")] = RGBColor(
        r=0, g=0, b=255
    )


class HorizontalGradientOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    left_color: Annotated[RGBColor, Field(description="Left color")] = RGBColor(
        r=0, g=0, b=0
    )
    right_color: Annotated[RGBColor, Field(description="Right color")] = RGBColor(
        r=0, g=0, b=255
    )


class VerticalGradientOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    top_color: Annotated[RGBColor, Field(description="Top color")] = RGBColor(
        r=0, g=0, b=0
    )
    bottom_color: Annotated[RGBColor, Field(description="Bottom color")] = RGBColor(
        r=0, g=0, b=255
    )


class ImageMaskOptions(BaseModel):
    back_color: Annotated[RGBColor, Field(description="Background color")] = RGBColor(
        r=255, g=255, b=255
    )
    color_mask_image: Annotated[
        str, Field(description="Base64-encoded image path for mask")
    ]


class QrColorMask(BaseModel):
    type: Annotated[QrColorMaskType, Field(description="Type of color mask")]
    options: Annotated[
        Union[
            SolidFillOptions,
            RadialGradientOptions,
            SquareGradientOptions,
            HorizontalGradientOptions,
            VerticalGradientOptions,
            ImageMaskOptions,
        ],
        Field(description="Options corresponding to the color mask type"),
    ]


class QrFormat(str, Enum):
    png = "png"
    jpeg = "jpeg"
    webp = "webp"
    svg = "svg"


class QrOutput(BaseModel):
    format: Annotated[QrFormat, Field(description="Output format of the QR code", json_schema_extra={"example": "png"})] = QrFormat.png  # type: ignore[call-arg]
    as_json: Annotated[bool, Field(description="Return as JSON data URI if True", json_schema_extra={"example": False})] = False  # type: ignore[call-arg]


class QrErrorCorrection(str, Enum):
    L = "L"  # ~7%
    M = "M"  # ~15%
    Q = "Q"  # ~25%
    H = "H"  # ~30%


class ResamplingFilter(str, Enum):
    NEAREST = "nearest"
    BOX = "box"
    BILINEAR = "bilinear"
    HAMMING = "hamming"
    BICUBIC = "bicubic"
    LANCZOS = "lanczos"


class QrLogoConfiguration(BaseModel):
    image: Annotated[str, Field(description="Base64-encoded logo image data.")]
    ratio: Annotated[
        float,
        Field(
            description="Ratio of the logo size to the QR code size (0.0 to 1.0).",
            ge=0.0,
            le=1.0,
            json_schema_extra={"example": 0.25},
        ),
    ] = 0.25
    filter: Annotated[
        ResamplingFilter,
        Field(
            description="PIL image resampling filter to use when resizing the logo.",
            json_schema_extra={"example": ResamplingFilter.LANCZOS},
        ),
    ] = ResamplingFilter.LANCZOS


class CreateQrRequest(BaseModel):
    data: Annotated[str, Field(description="The content to encode in the QR code", json_schema_extra={"example": "https://example.com"})]  # type: ignore[call-arg]
    version: Annotated[Optional[conint(ge=1, le=40)], Field(description="QR code version (1–40). None for auto-fit", json_schema_extra={"example": None})] = None  # type: ignore[valid-type]
    fit: Annotated[Optional[bool], Field(description="Automatically fit QR code if version is None", json_schema_extra={"example": True})] = True  # type: ignore[call-arg]
    error_correction: Annotated[
        QrErrorCorrection,
        Field(  # type: ignore[call-arg]
            description="Error correction level. L (~7%), M (~15%), Q (~25%), H (~30%). Must be 'H' if a logo is provided.",
            json_schema_extra={"example": QrErrorCorrection.M},
        ),
    ] = QrErrorCorrection.M
    mask_pattern: Annotated[Optional[conint(ge=0, le=7)], Field(description="A mask pattern changes which modules are dark and which are light according to a particular rule.", json_schema_extra={"example": None})] = None  # type: ignore[valid-type]
    output: Annotated[QrOutput, Field(description="Output format and options", json_schema_extra={"example": {"format": "png", "as_json": False}})] = QrOutput()  # type: ignore[call-arg]
    box_size: Annotated[Optional[int], Field(description="Size of each QR code box in pixels", json_schema_extra={"example": 10})] = 10  # type: ignore[call-arg]
    border: Annotated[Optional[int], Field(description="Width of the border around the QR code", json_schema_extra={"example": 4})] = 4  # type: ignore[call-arg]
    module_drawer: Annotated[
        Union[
            SvgSquareDrawerOptions,
            SvgCircleDrawerOptions,
            SvgPathSquareDrawerOptions,
            SvgPathCircleDrawerOptions,
            SquareModuleDrawerOptions,
            GappedSquareModuleDrawerOptions,
            CircleModuleDrawerOptions,
            RoundedModuleDrawerOptions,
            VerticalBarsDrawerOptions,
            HorizontalBarsDrawerOptions,
        ],
        Field(
            discriminator="type",
            description="Module drawer style and its associated options. The 'type' determines the specific drawer model and its fields (e.g., 'ratio').",
            json_schema_extra={"example": {"type": "rounded_module", "ratio": 0.6}},
        ),
    ] = SquareModuleDrawerOptions()  # type: ignore[call-arg]
    logo: Annotated[
        Optional[QrLogoConfiguration],
        Field(
            description="Optional configuration for an embedded logo image in the center. Requires 'error_correction' to be 'H' and output format to be PIL-based (e.g., png, jpeg, webp).",
            json_schema_extra={"example": None},
        ),
    ] = None  # type: ignore[call-arg]
    color_mask: Annotated[Optional[QrColorMask], Field(description="Optional color mask to style the QR code", json_schema_extra={"example": None})] = None  # type: ignore[call-arg]
    fill_color: Annotated[RGBColor, Field(description="Foreground color of the QR code", json_schema_extra={"example": {"r": 0, "g": 0, "b": 0}})] = RGBColor(r=0, g=0, b=0)  # type: ignore[call-arg]
    back_color: Annotated[RGBColor, Field(description="Background color of the QR code", json_schema_extra={"example": {"r": 255, "g": 255, "b": 255}})] = RGBColor(r=255, g=255, b=255)  # type: ignore[call-arg]
    eye_drawer: Annotated[
        Optional[Dict[QrEyePosition, QrEyeConfiguration]],
        Field(
            description="Custom styling for the position adjustment patterns (eyes). Keys must be 'top_left', 'top_right', or 'bottom_left'. "
            "Only eyes present in this dictionary will be customized.",
            json_schema_extra={
                "example": {
                    "top_left": {
                        "outer": {
                            "radius": 0.33,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 0.33,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                    "top_right": {
                        "outer": {
                            "radius": 0.66,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 0.66,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                    "bottom_left": {
                        "outer": {
                            "radius": 1.0,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 1.0,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                }
            },
        ),
    ] = None  # type: ignore[call-arg]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": "https://example.com",
                "version": 5,
                "fit": True,
                "error_correction": "M",
                "mask_pattern": None,
                "output": {"format": "png", "as_json": False},
                "box_size": 10,
                "border": 4,
                "module_drawer": {
                    "type": "svg_circle",
                    "ratio": 0.8,
                },
                "logo": {
                    "image": "BASE64_ENCODED_IMAGE_STRING",
                    "ratio": 0.25,
                    "resample": "lanczos",
                },
                "color_mask": {
                    "type": "solid",
                    "options": {
                        "front_color": {"r": 0, "g": 0, "b": 0},
                        "back_color": {"r": 255, "g": 255, "b": 255},
                    },
                },
                "fill_color": {"r": 0, "g": 0, "b": 0},
                "back_color": {"r": 255, "g": 255, "b": 255},
                "eye_drawer": {
                    "top_left": {
                        "outer": {
                            "radius": 0.33,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 0.33,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                    "top_right": {
                        "outer": {
                            "radius": 0.66,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 0.66,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                    "bottom_left": {
                        "outer": {
                            "radius": 1.0,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                        "inner": {
                            "radius": 1.0,
                            "outline": {"r": 0, "g": 0, "b": 0},
                            "corners": [True, True, True, True],
                        },
                    },
                },
            }
        }
    )

    @model_validator(mode="after")
    def validate_module_drawer_for_format(self):
        # Now we check the class of the module_drawer instance itself
        module_drawer = self.module_drawer
        output_format = self.output.format

        svg_classes = (
            SvgSquareDrawerOptions,
            SvgCircleDrawerOptions,
            SvgPathSquareDrawerOptions,
            SvgPathCircleDrawerOptions,
        )

        pil_classes = (
            SquareModuleDrawerOptions,
            GappedSquareModuleDrawerOptions,
            CircleModuleDrawerOptions,
            RoundedModuleDrawerOptions,
            VerticalBarsDrawerOptions,
            HorizontalBarsDrawerOptions,
        )

        if output_format == QrFormat.png and isinstance(module_drawer, svg_classes):
            raise ValueError(
                f"Cannot use SVG module drawer '{module_drawer.type}' with PNG output."
            )
        if output_format == QrFormat.svg and isinstance(module_drawer, pil_classes):
            raise ValueError(
                f"Cannot use non-SVG module drawer '{module_drawer.type}' with SVG output."
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def validate_logo_error_correction(cls, values):
        logo = values.get("logo")
        ec = values.get("error_correction", QrErrorCorrection.M)
        if logo and ec not in (QrErrorCorrection.H,):
            raise ValueError(
                "If a logo is provided 'error_correction' must be set to 'H'."
            )
        return values
