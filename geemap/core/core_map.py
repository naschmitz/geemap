# import abc
import math
from typing import Any, Dict, List, Optional, Sequence
import webbrowser

import ipyleaflet
import ipywidgets

from . import core_widgets
from . import core_utils


class MapInterface:
    """Interface that all maps should conform to."""

    @property
    def zoom(self) -> int:
        """Returns the current zoom level of the map."""
        raise NotImplementedError()

    @zoom.setter
    def zoom(self, value: int) -> None:
        """Sets the current zoom level of the map."""
        raise NotImplementedError()

    @property
    def center(self) -> Sequence:
        """Returns the current center of the map (lat, lon)."""
        raise NotImplementedError()

    @center.setter
    def center(self, value: Sequence) -> None:
        """Sets the current center of the map (lat, lon)."""
        del value  # Unused.
        raise NotImplementedError()

    @property
    def scale(self) -> float:
        """Returns the approximate pixel scale of the current map view, in meters."""
        raise NotImplementedError()

    @property
    def width(self) -> str:
        """Returns the current width of the map."""
        raise NotImplementedError()

    @width.setter
    def width(self, value: str) -> None:
        """Sets the width of the map."""
        del value  # Unused.
        raise NotImplementedError()

    @property
    def height(self) -> str:
        """Returns the current height of the map."""
        raise NotImplementedError()

    @height.setter
    def height(self, value: str) -> None:
        """Sets the height of the map."""
        del value  # Unused.
        raise NotImplementedError()

    # def add(self) -> None:
    #     """Adds a control to the map."""
    #     raise NotImplementedError()

    def add_widget(self, widget: str, position: str, **kwargs) -> None:
        """Adds a widget to the map."""
        del widget, position, kwargs  # Unused.
        raise NotImplementedError()

    def remove_widget(self, widget: str) -> None:
        """Removes a widget to the map."""
        del widget  # Unused.
        raise NotImplementedError()

    # def add_zoom_control(self, position: str) -> None:
    #     """Adds the zoom widget to the map."""
    #     raise NotImplementedError()

    # def add_fullscreen_control(self, position: str) -> None:
    #     """Adds the fullscreen widget to the map."""
    #     raise NotImplementedError()

    # def add_scale_control(self, position: str) -> None:
    #     """Adds the scale widget to the map."""
    #     raise NotImplementedError()

    # def add_measure_control(self, position: str) -> None:
    #     """Adds the measure widget to the map."""
    #     raise NotImplementedError()

    # def add_attribution_control(self, position: str) -> None:
    #     """Adds the attribution widget to the map."""
    #     raise NotImplementedError()

    # def add_toolbar(self, position: str) -> None:
    #     """Adds the toolbar widget to the map."""
    #     raise NotImplementedError()

    # def add_inspector(
    #     self,
    #     position: str,
    #     layers: Optional[List[str]],
    #     visible: bool,
    #     decimals: int,
    #     opened: bool,
    #     show_close_button: bool,
    # ) -> None:
    #     """Adds the inspector widget to the map."""
    #     raise NotImplementedError()


class LeafletMap(ipyleaflet.Map, MapInterface):
    """The Map class inherits the ipyleaflet Map class.

    Args:
        center (list, optional): Center of the map (lat, lon). Defaults to [0, 0].
        zoom (int, optional): Zoom level of the map. Defaults to 2.
        height (str, optional): Height of the map. Defaults to "600px".
        width (str, optional): Width of the map. Defaults to "100%".

    Returns:
        object: ipyleaflet map object.
    """

    _KWARG_DEFAULTS: Dict[str, Any] = {
        "center": [0, 0],
        "zoom": 2,
    }

    # zoom property handled by ipyleaflet.

    # center property handled by ipyleaflet.

    @property
    def width(self) -> str:
        return self.layout.width

    @width.setter
    def width(self, value: str) -> None:
        self.layout.width = value

    @property
    def height(self) -> str:
        return self.layout.height

    @height.setter
    def height(self, value: str) -> None:
        self.layout.height = value

    @property
    def scale(self) -> float:
        return core_utils.get_scale(self.center, self.zoom)

    def __init__(self, **kwargs):
        self.width: str = kwargs.pop("width", "100%")
        self.height: str = kwargs.pop("height", "600px")

        parsed_kwargs = self._parse_all_kwargs(kwargs)
        super().__init__(**parsed_kwargs)

        self._toolbar: Optional[core_widgets.Toolbar] = None
        self._toolbar_control: Optional[ipyleaflet.WidgetControl] = None
        self._inspector: Optional[core_widgets.Inspector] = None
        self._inspector_control: Optional[ipyleaflet.WidgetControl] = None

        self._reset_controls()

    def add_widget(self, widget: str, position: str = "topright", **kwargs) -> None:
        """Adds a widget to the map."""

        # Basic controls:
        #   - Can only be added to the map once.
        #   - Have a constructor that takes a position arg.
        #   - Don't need to be stored as instance vars.
        basic_controls: Dict[str, ipyleaflet.Control] = {
            "zoom_control": (ipyleaflet.ZoomControl, {}),
            "fullscreen_control": (ipyleaflet.FullScreenControl, {}),
            "scale_control": (ipyleaflet.ScaleControl, {}),
            "measure_control": (
                ipyleaflet.MeasureControl,
                {"active_color": "orange", "primary_length_unit": "kilometers"},
            ),
            "attribution_control": (ipyleaflet.AttributionControl, {}),
        }

        if widget in basic_controls:
            basic_control = basic_controls[widget]

            # Check if widget is already on the map.
            for control in self.controls:
                if isinstance(control, basic_control[0]):
                    return
            new_kwargs = {**basic_control[1], **kwargs}
            self.add(basic_control[0](position=position, **new_kwargs))

        elif widget == "toolbar" and self._toolbar_control is None:
            self._toolbar = core_widgets.Toolbar(
                self, self._get_toolbar_tools(), **kwargs
            )
            self._toolbar_control = ipyleaflet.WidgetControl(
                widget=self._toolbar, position=position
            )
            self.add(self._toolbar_control)

        elif widget == "inspector" and self._inspector_control is None:
            self._inspector = core_widgets.Inspector(self, **kwargs)
            self._inspector.on_close = lambda: self.remove_widget("inspector")
            self._inspector_control = ipyleaflet.WidgetControl(
                widget=self._inspector, position=position
            )
            self.add(self._inspector_control)

    def remove_widget(self, widget: str) -> None:
        """Removes a widget to the map."""

        basic_controls: Dict[str, ipyleaflet.Control] = {
            "zoom_control": ipyleaflet.ZoomControl,
            "fullscreen_control": ipyleaflet.FullScreenControl,
            "scale_control": ipyleaflet.ScaleControl,
            "measure_control": ipyleaflet.MeasureControl,
            "attribution_control": ipyleaflet.AttributionControl,
        }

        if widget in basic_controls:
            for control in self.controls:
                if isinstance(control, basic_controls[widget][0]):
                    self.remove_control(control)
                    control.close()

        elif widget == "toolbar" and self._toolbar_control:
            if self._toolbar_control in self.controls:
                self.remove_control(self._toolbar_control)
            self._toolbar_control.close()
            self._toolbar_control = None
            self._toolbar = None

        elif widget == "inspector" and self._inspector_control:
            if self._toolbar:
                self._toolbar.set_widget_value("info", False)
            if self._inspector_control in self.controls:
                self.remove_control(self._inspector_control)
            self._inspector_control.close()
            self._inspector_control = None
            self._inspector = None

    def _open_help_page(self, host_map: MapInterface, selected: bool) -> None:
        del host_map  # Unused.
        if selected:
            webbrowser.open_new_tab("https://geemap.org")

    def _get_toolbar_tools(self) -> List[core_widgets.Toolbar.Item]:
        return [
            core_widgets.Toolbar.Item(
                icon="info",
                tooltip="Inspector",
                callback=lambda m, selected: m.add_widget("inspector")
                if selected
                else None,
            ),
            core_widgets.Toolbar.Item(
                icon="question", tooltip="Get help", callback=self._open_help_page
            ),
        ]

    def _reset_controls(self) -> None:
        self.clear_controls()

        controls: Dict[str, List[str]] = {
            "topleft": ["zoom_control", "fullscreen_control"],
            "bottomleft": ["scale_control", "measure_control"],
            "topright": ["toolbar"],
            "bottomright": ["attribution_control"],
        }
        for position, widgets in controls.items():
            for widget in widgets:
                self.add_widget(widget, position=position)

    def _parse_all_kwargs(self, kwargs):
        ret_kwargs = {}
        for kwarg, default in self._KWARG_DEFAULTS.items():
            ret_kwargs[kwarg] = kwargs.pop(kwarg, default)
        ret_kwargs.update(kwargs)
        return ret_kwargs


# def add_zoom_control(self, position: str) -> None:
#     self.add(ipyleaflet.ZoomControl(position=position))

# def add_fullscreen_control(self, position: str) -> None:
#     self.add(ipyleaflet.FullScreenControl(position=position))

# def add_scale_control(self, position: str) -> None:
#     self.add(ipyleaflet.ScaleControl(position=position))

# def add_measure_control(self, position: str) -> None:
#     self.add(
#         ipyleaflet.MeasureControl(
#             position=position,
#             active_color="orange",
#             primary_length_unit="kilometers",
#         )
#     )

# def add_attribution_control(self, position: str) -> None:
#     self.add(ipyleaflet.AttributionControl(position=position))

# def add_toolbar(self, position: str) -> None:
#     self._toolbar = core_widgets.Toolbar(self, self._get_toolbar_tools())
#     self._toolbar_control = ipyleaflet.WidgetControl(
#         widget=self._toolbar, position=position
#     )
#     self.add(self._toolbar_control)

# def add_inspector(
#     self,
#     position: str = "topright",
#     layers: Optional[List[str]] = None,
#     visible: bool = True,
#     decimals: int = 2,
#     opened: bool = True,
#     show_close_button: bool = True,
# ) -> None:
#     """Add the Inspector GUI to the map.

#     Args:
#         position (str, optional): The position of the Inspector GUI. Defaults to "topright".
#         layers (str | list, optional): The names of the layers to be included. Defaults to None.
#         visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
#         decimals (int, optional): The number of decimal places to round the coordinates. Defaults to 2.
#         opened (bool, optional): Whether the control is opened. Defaults to True.
#         show_close_button (bool, optional): Whether the close button is shown. Defaults to True.
#     """
#     if self._inspector_control:
#         return

#     self._inspector = core_widgets.Inspector(
#         self, layers, visible, decimals, opened, show_close_button
#     )
#     self._inspector.on_close = self.remove_inspector
#     self._inspector_control = ipyleaflet.WidgetControl(
#         widget=self._inspector, position=position
#     )
#     self.add(self._inspector_control)
