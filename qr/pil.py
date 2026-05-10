import abc
import math
from typing import TYPE_CHECKING, Any, Union, ClassVar, Optional, Dict, Tuple, cast

from PIL import ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)
from qrcode.main import QRCode

from qr.schemas import (
    QrModuleDrawer,
    PilBaseModuleDrawerOptions,
    GappedSquareModuleDrawerOptions,
    RoundedModuleDrawerOptions,
    VerticalBarsDrawerOptions,
    HorizontalBarsDrawerOptions,
)

if TYPE_CHECKING:
    from qrcode.image.base import BaseImage
    from qrcode.main import ActiveWithNeighbors, QRCode

    # We assume the necessary configuration types (like QrEyeConfiguration)
    # would be imported here in a real setup, but we use Dict[str, Any] for now.

# Define a type alias for clarity: (max_integer_radius_pixels, max_safe_factor)
RadiusMetrics = tuple[int, float]


class EyeRadiusCalculator:
    OUTER_EYE_MODULES: ClassVar[int] = 7  # The main finder pattern is always 7x7
    INNER_EYEBALL_MODULES: ClassVar[int] = 3  # The central square is always 3x3

    def __init__(self, box_size: int):
        """
        Initializes the calculator with the pixel size of a single QR module.
        """
        if box_size <= 0:
            raise ValueError("box_size must be a positive integer.")
        self.box_size = box_size

    @staticmethod
    def _calculate_metrics(module_count: int, box_size: int) -> RadiusMetrics:
        """
        Core logic to calculate the maximum safe radius and factor.

        Formula: floor((D - 3) / 2) -> The '- 3' is the safety margin for PIL.
        """
        # 1. Calculate the Total Dimension (D) in pixels.
        total_dimension_pixels = module_count * box_size

        # 2. Calculate the Maximum Integer Radius (r_max).
        if total_dimension_pixels < 3:
            # Ensure the dimension is large enough for the formula's safety margin
            return 0, 0.0

        max_integer_radius_pixels = math.floor((total_dimension_pixels - 3) / 2)

        # 3. Calculate the Maximum Safe Factor (F_max).
        max_safe_factor = max_integer_radius_pixels / box_size

        return max_integer_radius_pixels, max_safe_factor

    def get_outer_eye_metrics(self) -> RadiusMetrics:
        """
        Returns the max radius metrics for the Outer Eye (7 modules).
        """
        return self._calculate_metrics(self.OUTER_EYE_MODULES, self.box_size)

    def get_inner_eyeball_metrics(self) -> RadiusMetrics:
        """
        Returns the max radius metrics for the Inner Eyeball (3 modules).
        """
        return self._calculate_metrics(self.INNER_EYEBALL_MODULES, self.box_size)

    def get_max_factor(self, component: str) -> float:
        """
        Utility method to get the maximum safe factor (F_max) for a component.
        """
        if component.lower() == "outer":
            return self.get_outer_eye_metrics()[1]
        elif component.lower() == "inner":
            return self.get_inner_eyeball_metrics()[1]
        else:
            raise ValueError("Component must be 'outer' or 'inner'.")

    def calculate_actual_factor_from_normalized(
        self, component: str, normalized_value: Union[int, float]
    ) -> float:
        """
        Maps a user's normalized value (0.0 to 1.0, representing 0% to 100%)
        to the actual radius factor required by the PIL drawing function.
        """

        # Clamp the input to ensure it is within the safe range [0.0, 1.0]
        clamped_value = max(0.0, min(1.0, float(normalized_value)))

        # Get the maximum safe factor (F_max) for the specified component
        max_factor = self.get_max_factor(component)

        # F_actual = Normalized_Value * F_max
        actual_factor = clamped_value * max_factor

        return actual_factor


class BaseEyeDrawer(abc.ABC):
    needs_processing = True
    needs_neighbors = False
    factory: "StyledPilImageEyeDrawer"

    def __init__(self):
        self.img = None

    def initialize(self, img: "BaseImage") -> None:
        """
        Initializes the drawer with the image. The 'img' passed here is actually
        the image factory instance (StyledPilImageEyeDrawer), so we set factory right away.
        """
        self.img = cast("StyledPilImageEyeDrawer", img)
        self.factory = self.img

    def draw(self):
        # North-West Eye (NW)
        (nw_eye_top, _), (_, nw_eye_bottom) = (
            self.factory.pixel_box(0, 0),
            self.factory.pixel_box(6, 6),
        )
        (nw_eyeball_top, _), (_, nw_eyeball_bottom) = (
            self.factory.pixel_box(2, 2),
            self.factory.pixel_box(4, 4),
        )
        self.draw_nw_eye((nw_eye_top, nw_eye_bottom))
        self.draw_nw_eyeball((nw_eyeball_top, nw_eyeball_bottom))

        # North-East Eye (NE)
        (ne_eye_top, _), (_, ne_eye_bottom) = (
            self.factory.pixel_box(0, self.factory.width - 7),
            self.factory.pixel_box(6, self.factory.width - 1),
        )
        (ne_eyeball_top, _), (_, ne_eyeball_bottom) = (
            self.factory.pixel_box(2, self.factory.width - 5),
            self.factory.pixel_box(4, self.factory.width - 3),
        )
        self.draw_ne_eye((ne_eye_top, ne_eye_bottom))
        self.draw_ne_eyeball((ne_eyeball_top, ne_eyeball_bottom))

        # South-West Eye (SW)
        (sw_eye_top, _), (_, sw_eye_bottom) = (
            self.factory.pixel_box(self.factory.width - 7, 0),
            self.factory.pixel_box(self.factory.width - 1, 6),
        )
        (sw_eyeball_top, _), (_, sw_eyeball_bottom) = (
            self.factory.pixel_box(self.factory.width - 5, 2),
            self.factory.pixel_box(self.factory.width - 3, 4),
        )
        self.draw_sw_eye((sw_eye_top, sw_eye_bottom))
        self.draw_sw_eyeball((sw_eyeball_top, sw_eyeball_bottom))

    @abc.abstractmethod
    def draw_nw_eye(self, position): ...

    @abc.abstractmethod
    def draw_nw_eyeball(self, position): ...

    @abc.abstractmethod
    def draw_ne_eye(self, position): ...

    @abc.abstractmethod
    def draw_ne_eyeball(self, position): ...

    @abc.abstractmethod
    def draw_sw_eye(self, position): ...

    @abc.abstractmethod
    def draw_sw_eyeball(self, position): ...


def _normalize_color(
    color_input: Any, fallback_color: str = "black"
) -> Union[str, Tuple[int, int, int], None]:
    """
    Converts configuration color types (dict, bool) into a format PIL understands
    (str, (R, G, B) tuple, or None).
    """
    if color_input is None:
        return None

    # Handle dictionary color format (e.g., {'r': 255, 'g': 0, 'b': 0})
    if isinstance(color_input, dict):
        if "r" in color_input and "g" in color_input and "b" in color_input:
            try:
                # Convert to (R, G, B) tuple expected by PIL
                return (color_input["r"], color_input["g"], color_input["b"])
            except TypeError:
                # Fallback if keys exist but values aren't ints
                return fallback_color

    # Handle boolean (False means no color/None)
    if color_input is False:
        return None

    # Handle boolean (True means use fallback color)
    if color_input is True:
        return fallback_color

    # Assume the color is already a valid string or tuple
    return color_input


class ConfigurableEyeDrawer(BaseEyeDrawer):
    """
    Draws the finder patterns (eyes) using styling configured by the user,
    dynamically calculating the safe radius factor based on box_size and
    a normalized radius value (0.0-1.0).

    QR Code Validity Rule:
    - Outer eye (7x7 frame) must NOT be filled.
    - Inner eyeball (3x3 square) must be filled.
    This behavior is now enforced, ignoring 'fill' in configuration.
    """

    # Default configuration. The 'fill' key is set to None/color based on the logic below.
    DEFAULT_CONFIG: ClassVar[Dict[str, Any]] = {
        # 'fill' is ignored for outer, it is always False (None)
        "outer": {
            "radius": 0.0,
            "outline": "black",
            "corners": [True, True, True, True],
        },
        # 'fill' is ignored for inner, it is always True (outline color)
        "inner": {
            "radius": 0.0,
            "outline": "black",
            "corners": [True, True, True, True],
        },
    }

    def __init__(self, eye_config_map: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Args:
            eye_config_map: A map from eye position ('top_left', etc.) to
                            the QrEyeConfiguration object (as a dictionary).
        """
        super().__init__()
        self.config_map = eye_config_map or {}
        self.calculator: Optional[EyeRadiusCalculator] = None

    def initialize(self, img: "BaseImage") -> None:
        """Initializes the drawer with the image and sets up the calculator."""

        # 1. First, call the super() to set self.img and self.factory
        super().initialize(img)

        # 2. Now self.factory is guaranteed to be set, and we can use its properties
        if hasattr(self.factory, "box_size") and self.factory.box_size > 0:
            self.calculator = EyeRadiusCalculator(box_size=self.factory.box_size)
        else:
            raise ValueError("Factory must have a valid positive 'box_size' attribute.")

    def _get_draw_params(self, position: str, component: str) -> Dict[str, Any]:
        """
        Retrieves the configuration for a specific eye component, enforces
        the fixed fill rule, and calculates the actual radius factor.
        """
        if not self.calculator:
            raise RuntimeError("EyeRadiusCalculator not initialized.")

        # 1. Determine which configuration to use (custom or default)
        eye_config = self.config_map.get(position)

        # Get the component model (e.g., the 'outer' or 'inner' Pydantic object)
        component_config_model = None
        if eye_config:
            # Note: We rely on the Pydantic model dump/dict access for user config
            component_config_model = getattr(eye_config, component, None)

        if component_config_model:
            # If the Pydantic model for the component exists, dump it to a
            # standard dictionary for consistent access using .get().
            component_config = component_config_model.model_dump()
        else:
            component_config = self.DEFAULT_CONFIG[component]

        # 2. Extract and Normalize OUTLINE color
        # This will be the color of the module itself.
        raw_outline_value = component_config.get("outline", "black")
        final_outline = _normalize_color(raw_outline_value, fallback_color="black")

        # 3. Enforce fixed FILL logic for QR code validity:
        # Outer eye must NOT be filled (None), Inner eyeball must be filled (outline color).
        is_inner = component == "inner"

        if is_inner:
            # Inner eyeball must be filled. Use the normalized outline color as the fill.
            final_fill = final_outline
        else:
            # Outer frame must not be filled (transparent).
            final_fill = None

        # 4. Extract normalized radius
        normalized_radius = component_config.get("radius", 0.0)

        # 5. Calculate actual factor (Actual Factor = Normalized_Value * F_max)
        actual_factor = self.calculator.calculate_actual_factor_from_normalized(
            component=component, normalized_value=normalized_radius
        )

        return {
            "fill": final_fill,
            "outline": final_outline,
            "radius_factor": actual_factor,
            "corners": component_config.get("corners", [True, True, True, True]),
            # Width is used for the outline of the outer eye (7x7 frame)
            "width": self.factory.box_size if component == "outer" else 1,
        }

    def _draw_eye_component(
        self, position_name: str, component_name: str, position: tuple
    ):
        """Generic method to draw either the outer eye or the inner eyeball."""
        draw = ImageDraw.Draw(self.img)

        # 1. Get drawing parameters, including the calculated factor
        params = self._get_draw_params(position_name, component_name)

        # 2. Calculate final radius in pixels (PIL requires pixels, not factor)
        # radius_pixels = factor * box_size
        radius_pixels = params["radius_factor"] * self.factory.box_size

        # 3. Draw the rounded rectangle
        draw.rounded_rectangle(
            position,
            fill=params["fill"],
            width=params["width"],
            outline=params["outline"],
            radius=radius_pixels,
            corners=params["corners"],
        )

    # North-West Eye implementations (uses 'top_left' key)
    def draw_nw_eye(self, position):
        self._draw_eye_component("top_left", "outer", position)

    def draw_nw_eyeball(self, position):
        self._draw_eye_component("top_left", "inner", position)

    # North-East Eye implementations (uses 'top_right' key)
    def draw_ne_eye(self, position):
        self._draw_eye_component("top_right", "outer", position)

    def draw_ne_eyeball(self, position):
        self._draw_eye_component("top_right", "inner", position)

    # South-West Eye implementations (uses 'bottom_left' key)
    def draw_sw_eye(self, position):
        self._draw_eye_component("bottom_left", "outer", position)

    def draw_sw_eyeball(self, position):
        self._draw_eye_component("bottom_left", "inner", position)


class StyledPilImageEyeDrawer(StyledPilImage):
    def drawrect_context(self, row: int, col: int, qr: QRCode[Any]):
        box = self.pixel_box(row, col)
        if self.is_eye(row, col):
            drawer = self.eye_drawer
            if getattr(self.eye_drawer, "needs_processing", False):
                return
        else:
            drawer = self.module_drawer

        is_active: Union[bool, ActiveWithNeighbors] = (
            qr.active_with_neighbors(row, col)
            if drawer.needs_neighbors
            else bool(qr.modules[row][col])
        )

        drawer.drawrect(box, is_active)

    def process(self) -> None:
        if getattr(self.eye_drawer, "needs_processing", False):
            # Ensure the eye drawer is initialized and ready
            self.eye_drawer.initialize(self)
            self.eye_drawer.draw()  # type: ignore[attr-defined]
        super().process()


def create_pil_drawer_instance_factory(
    drawer_options: PilBaseModuleDrawerOptions,
) -> Any:
    """Returns an instantiated ModuleDrawer object based on options for PIL output."""

    drawer_map = {
        QrModuleDrawer.SquareModuleDrawer.value: SquareModuleDrawer,
        QrModuleDrawer.GappedSquareModuleDrawer.value: GappedSquareModuleDrawer,
        QrModuleDrawer.CircleModuleDrawer.value: CircleModuleDrawer,
        QrModuleDrawer.RoundedModuleDrawer.value: RoundedModuleDrawer,
        QrModuleDrawer.VerticalBarsDrawer.value: VerticalBarsDrawer,
        QrModuleDrawer.HorizontalBarsDrawer.value: HorizontalBarsDrawer,
    }

    kwargs: Dict[str, Any] = {}

    if isinstance(drawer_options, GappedSquareModuleDrawerOptions):
        kwargs["size_ratio"] = drawer_options.ratio
    elif isinstance(drawer_options, RoundedModuleDrawerOptions):
        kwargs["radius_ratio"] = drawer_options.ratio
    elif isinstance(drawer_options, VerticalBarsDrawerOptions):
        kwargs["horizontal_shrink"] = drawer_options.shrink
    elif isinstance(drawer_options, HorizontalBarsDrawerOptions):
        kwargs["vertical_shrink"] = drawer_options.shrink

    drawer_instance = drawer_map.get(drawer_options.type)

    if not drawer_instance:
        raise ValueError(f"Unknown PIL drawer type: {drawer_options.type}")

    return drawer_instance(**kwargs)
