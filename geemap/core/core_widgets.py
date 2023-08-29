import dataclasses
from typing import Callable

import ee
import ipyevents
import ipytree
import ipywidgets

from . import core_utils

# from . import common


class Toolbar(ipywidgets.VBox):
    """A toolbar that can be added to the map."""

    @dataclasses.dataclass
    class Item:
        """A representation of an item in the toolbar.

        Attributes:
            icon: The icon to use for the item, from https://fontawesome.com/icons.
            tooltip: The tooltip text to show a user on hover.
            callback: A callback function to execute when the item icon is clicked.
                Its signature should be `callback(map, selected)`, where `map` is the
                host map and `selected` is a boolean indicating if the user selected
                or unselected the tool.
            reset: Whether to reset the selection after the callback has finished.
        """

        icon: str
        tooltip: str
        callback: Callable[[any, bool], None]
        reset: bool = True

    ICON_WIDTH = "32px"
    ICON_HEIGHT = "32px"
    NUM_COLS = 3

    _TOGGLE_TOOL_EXPAND_ICON = "plus"
    _TOGGLE_TOOL_EXPAND_TOOLTIP = "Expand toolbar"
    _TOGGLE_TOOL_COLLAPSE_ICON = "minus"
    _TOGGLE_TOOL_COLLAPSE_TOOLTIP = "Collapse toolbar"

    def __init__(self, host_map, main_tools, extra_tools=None):
        """Adds a toolbar with `main_tools` and `extra_tools` to the `host_map`."""
        if not main_tools:
            raise ValueError("A toolbar cannot be initialized without `main_tools`.")
        self.host_map = host_map
        self.toggle_tool = Toolbar.Item(
            icon=self._TOGGLE_TOOL_EXPAND_ICON,
            tooltip=self._TOGGLE_TOOL_EXPAND_TOOLTIP,
            callback=self._toggle_callback,
        )
        self.accessory_widget = None
        self.on_layers_toggled = None

        if extra_tools:
            all_tools = main_tools + [self.toggle_tool] + extra_tools
        else:
            all_tools = main_tools
        icons = [tool.icon for tool in all_tools]
        tooltips = [tool.tooltip for tool in all_tools]
        callbacks = [tool.callback for tool in all_tools]
        resets = [tool.reset for tool in all_tools]
        self.num_collapsed_tools = len(main_tools) + 1
        # -(-a//b) is the same as math.ceil(a/b)
        self.num_rows_expanded = -(-len(all_tools) // self.NUM_COLS)
        self.num_rows_collapsed = -(-self.num_collapsed_tools // self.NUM_COLS)

        self.all_widgets = [
            ipywidgets.ToggleButton(
                layout=ipywidgets.Layout(
                    width="auto", height="auto", padding="0px 0px 0px 4px"
                ),
                button_style="primary",
                icon=icons[i],
                tooltip=tooltips[i],
            )
            for i in range(len(all_tools))
        ]
        self.toggle_widget = self.all_widgets[len(main_tools)] if extra_tools else None

        # We start with a collapsed grid of just the main tools and the toggle one.
        self.grid = ipywidgets.GridBox(
            children=self.all_widgets[: self.num_collapsed_tools],
            layout=ipywidgets.Layout(
                width="109px",
                grid_template_columns=(self.ICON_WIDTH + " ") * self.NUM_COLS,
                grid_template_rows=(self.ICON_HEIGHT + " ") * self.num_rows_collapsed,
                grid_gap="1px 1px",
                padding="5px",
            ),
        )

        def curry_callback(callback, should_reset_after, widget):
            def returned_callback(change):
                if change["type"] != "change":
                    return
                # Unselect all other tool widgets.
                self._reset_others(widget)
                callback(self.host_map, change["new"])
                if should_reset_after:
                    widget.value = False

            return returned_callback

        for id, widget in enumerate(self.all_widgets):
            widget.observe(curry_callback(callbacks[id], resets[id], widget), "value")

        self.toolbar_button = ipywidgets.ToggleButton(
            value=False,
            tooltip="Toolbar",
            icon="wrench",
            layout=ipywidgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )

        self.layers_button = ipywidgets.ToggleButton(
            value=False,
            tooltip="Layers",
            icon="server",
            layout=ipywidgets.Layout(height="28px", width="72px"),
        )

        self.toolbar_header = ipywidgets.HBox()
        self.toolbar_header.children = [self.layers_button, self.toolbar_button]
        self.toolbar_footer = ipywidgets.VBox()
        self.toolbar_footer.children = [self.grid]

        self.toolbar_button.observe(self._toolbar_btn_click, "value")
        self.layers_button.observe(self._layers_btn_click, "value")

        super().__init__(children=[self.toolbar_button])
        toolbar_event = ipyevents.Event(
            source=self, watched_events=["mouseenter", "mouseleave"]
        )
        toolbar_event.on_dom_event(self._handle_toolbar_event)

    def reset(self):
        """Resets the toolbar so that no widget is selected."""
        for widget in self.all_widgets:
            widget.value = False

    def _reset_others(self, current):
        for other in self.all_widgets:
            if other is not current:
                other.value = False

    def set_widget_value(self, icon_name, value):
        for widget in self.all_widgets:
            if widget.icon == icon_name:
                widget.value = value

    def _toggle_callback(self, m, selected):
        del m  # unused
        if not selected:
            return
        if self.toggle_widget.icon == self._TOGGLE_TOOL_EXPAND_ICON:
            self.grid.layout.grid_template_rows = (
                self.ICON_HEIGHT + " "
            ) * self.num_rows_expanded
            self.grid.children = self.all_widgets
            self.toggle_widget.tooltip = self._TOGGLE_TOOL_COLLAPSE_TOOLTIP
            self.toggle_widget.icon = self._TOGGLE_TOOL_COLLAPSE_ICON
        elif self.toggle_widget.icon == self._TOGGLE_TOOL_COLLAPSE_ICON:
            self.grid.layout.grid_template_rows = (
                self.ICON_HEIGHT + " "
            ) * self.num_rows_collapsed
            self.grid.children = self.all_widgets[: self.num_collapsed_tools]
            self.toggle_widget.tooltip = self._TOGGLE_TOOL_EXPAND_TOOLTIP
            self.toggle_widget.icon = self._TOGGLE_TOOL_EXPAND_ICON

    def _handle_toolbar_event(self, event):
        if event["type"] == "mouseenter":
            self.children = [self.toolbar_header, self.toolbar_footer]
        elif event["type"] == "mouseleave":
            if not self.toolbar_button.value:
                self.children = [self.toolbar_button]
                self.toolbar_button.value = False
                self.layers_button.value = False

    def _toolbar_btn_click(self, change):
        if change["new"]:
            self.layers_button.value = False
            self.children = [self.toolbar_header, self.toolbar_footer]
        else:
            if not self.layers_button.value:
                self.children = [self.toolbar_button]

    def set_accessory_widget(self, value):
        self.accessory_widget = value
        if self.accessory_widget:
            self.toolbar_footer.children = [self.accessory_widget]
        else:
            self.toolbar_footer.children = [self.grid]

    def _layers_btn_click(self, change):
        if self.on_layers_toggled:
            self.on_layers_toggled(change["new"])


class Inspector(ipywidgets.VBox):
    """Inspector widget for Earth Engine data."""

    def __init__(
        self,
        host_map,
        names=None,
        visible=True,
        decimals=2,
        opened=True,
        show_close_button=True,
    ):
        """Creates an Inspector widget for Earth Engine data.

        Args:
            host_map (geemap.Map): The map to add the inspector widget to.
            names (list, optional): The list of layer names to be inspected. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            decimals (int, optional): The number of decimal places to round the values. Defaults to 2.
            opened (bool, optional): Whether the inspector is opened. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button. Defaults to True.
        """

        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating an inspector.")

        self._names = names
        self._visible = visible
        self._decimals = decimals
        self._opened = opened

        self.on_close = None

        self._expand_point_tree = False
        self._expand_pixels_tree = True
        self._expand_objects_tree = False

        host_map.default_style = {"cursor": "crosshair"}

        left_padded_square = ipywidgets.Layout(
            width="28px", height="28px", padding="0px 0px 0px 4px"
        )

        self.toolbar_button = ipywidgets.ToggleButton(
            value=opened, tooltip="Inspector", icon="info", layout=left_padded_square
        )
        self.toolbar_button.observe(self._on_toolbar_btn_click, "value")

        close_button = ipywidgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            button_style="primary",
            layout=left_padded_square,
        )
        close_button.observe(self._on_close_btn_click, "value")

        point_checkbox = self._create_checkbox("Point", self._expand_point_tree)
        pixels_checkbox = self._create_checkbox("Pixels", self._expand_pixels_tree)
        objects_checkbox = self._create_checkbox("Objects", self._expand_objects_tree)
        point_checkbox.observe(self._on_point_checkbox_changed, "value")
        pixels_checkbox.observe(self._on_pixels_checkbox_changed, "value")
        objects_checkbox.observe(self._on_objects_checkbox_changed, "value")
        self.inspector_checks = ipywidgets.HBox(
            children=[
                ipywidgets.Label(
                    "Expand", layout=ipywidgets.Layout(padding="0px 8px 0px 4px")
                ),
                point_checkbox,
                pixels_checkbox,
                objects_checkbox,
            ]
        )

        if show_close_button:
            self.toolbar_header = ipywidgets.HBox(
                children=[close_button, self.toolbar_button]
            )
        else:
            self.toolbar_header = ipywidgets.HBox(children=[self.toolbar_button])
        self.tree_output = ipywidgets.VBox(
            children=[],
            layout=ipywidgets.Layout(
                max_width="600px", max_height="300px", overflow="auto", display="block"
            ),
        )
        self._clear_inspector_output()

        host_map.on_interaction(self._on_map_interaction)
        self.toolbar_button.value = opened

        super().__init__(
            children=[self.toolbar_header, self.inspector_checks, self.tree_output]
        )

    def _create_checkbox(self, title, checked):
        layout = ipywidgets.Layout(width="auto", padding="0px 6px 0px 0px")
        return ipywidgets.Checkbox(
            description=title, indent=False, value=checked, layout=layout
        )

    def _on_map_interaction(self, **kwargs):
        latlon = kwargs.get("coordinates")
        if kwargs.get("type") == "click":
            self._on_map_click(latlon)

    def _on_map_click(self, latlon):
        if self.toolbar_button.value:
            self._host_map.default_style = {"cursor": "wait"}
            self._clear_inspector_output()

            nodes = [self._point_info(latlon)]
            pixels_node = self._pixels_info(latlon)
            if pixels_node.nodes:
                nodes.append(pixels_node)
            objects_node = self._objects_info(latlon)
            if objects_node.nodes:
                nodes.append(objects_node)

            self.tree_output.children = [ipytree.Tree(nodes=nodes)]
            self._host_map.default_style = {"cursor": "crosshair"}

    def _clear_inspector_output(self):
        self.tree_output.children = []
        self.children = []
        self.children = [self.toolbar_header, self.inspector_checks, self.tree_output]

    def _on_point_checkbox_changed(self, change):
        self._expand_point_tree = change["new"]

    def _on_pixels_checkbox_changed(self, change):
        self._expand_pixels_tree = change["new"]

    def _on_objects_checkbox_changed(self, change):
        self._expand_objects_tree = change["new"]

    def _on_toolbar_btn_click(self, change):
        if change["new"]:
            self._host_map.default_style = {"cursor": "crosshair"}
            self.children = [
                self.toolbar_header,
                self.inspector_checks,
                self.tree_output,
            ]
            self._clear_inspector_output()
        else:
            self.children = [self.toolbar_button]
            self._host_map.default_style = {"cursor": "default"}

    def _on_close_btn_click(self, change):
        if change["new"]:
            if self._host_map:
                self._host_map.default_style = {"cursor": "default"}
                self._host_map.on_interaction(self._on_map_interaction, remove=True)
            if self.on_close is not None:
                self.on_close()

    def _get_visible_map_layers(self):
        layers = {}
        if self._names is not None:
            names = [names] if isinstance(names, str) else self._names
            for name in names:
                if name in self._host_map.ee_layers:
                    layers[name] = self._host_map.ee_layers[name]
        else:
            layers = self._host_map.ee_layers
        return {k: v for k, v in layers.items() if v["ee_layer"].visible}

    def _root_node(self, title, nodes, **kwargs):
        return ipytree.Node(
            title,
            icon="archive",
            nodes=nodes,
            open_icon="plus-square",
            open_icon_style="success",
            close_icon="minus-square",
            close_icon_style="info",
            **kwargs,
        )

    def _point_info(self, latlon):
        scale = core_utils.get_scale(latlon, self._host_map.zoom)
        label = f"Point ({latlon[1]:.{self._decimals}f}, {latlon[0]:.{self._decimals}f}) at {int(scale)}m/px"
        nodes = [
            ipytree.Node(f"Longitude: {latlon[1]}"),
            ipytree.Node(f"Latitude: {latlon[0]}"),
            ipytree.Node(f"Zoom Level: {self._host_map.zoom}"),
            ipytree.Node(f"Scale (approx. m/px): {scale}"),
        ]
        return self._root_node(label, nodes, opened=self._expand_point_tree)

    def _query_point(self, latlon, ee_object):
        point = ee.Geometry.Point(latlon[::-1])
        scale = core_utils.get_scale(latlon, self._host_map.zoom)
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        if isinstance(ee_object, ee.Image):
            return ee_object.reduceRegion(ee.Reducer.first(), point, scale).getInfo()
        return None

    def _pixels_info(self, latlon):
        if not self._visible:
            return self._root_node("Pixels", [])

        layers = self._get_visible_map_layers()
        nodes = []
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            pixel = self._query_point(latlon, ee_object)
            if not pixel:
                continue
            pluralized_band = "band" if len(pixel) == 1 else "bands"
            ee_obj_type = ee_object.__class__.__name__
            label = f"{layer_name}: {ee_obj_type} ({len(pixel)} {pluralized_band})"
            layer_node = ipytree.Node(label, opened=self._expand_pixels_tree)
            for key, value in sorted(pixel.items()):
                if isinstance(value, float):
                    value = round(value, self._decimals)
                layer_node.add_node(ipytree.Node(f"{key}: {value}", icon="file"))
            nodes.append(layer_node)

        return self._root_node("Pixels", nodes)

    def _get_bbox(self, latlon):
        lat, lon = latlon
        delta = 0.005
        return ee.Geometry.BBox(lon - delta, lat - delta, lon + delta, lat + delta)

    def _objects_info(self, latlon):
        if not self._visible:
            return self._root_node("Objects", [])

        layers = self._get_visible_map_layers()
        point = ee.Geometry.Point(latlon[::-1])
        nodes = []
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            if isinstance(ee_object, ee.FeatureCollection):
                geom = ee.Feature(ee_object.first()).geometry()
                bbox = self._get_bbox(latlon)
                is_point = ee.Algorithms.If(
                    geom.type().compareTo(ee.String("Point")), point, bbox
                )
                ee_object = ee_object.filterBounds(is_point).first()
                tree_node = common.get_info(
                    ee_object, layer_name, self._expand_objects_tree, True
                )
                if tree_node:
                    nodes.append(tree_node)

        return self._root_node("Objects", nodes)
