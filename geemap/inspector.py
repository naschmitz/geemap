import os

import ee
import ipyevents
import ipyleaflet
import ipywidgets as widgets
from ipyfilechooser import FileChooser
from IPython.core.display import display

from .common import *
from .timelapse import *


class Inspector(widgets.VBox):

    host_map: any = None
    expand_point: bool = False
    expand_pixels: bool = True
    expand_objects: bool = False

    def __init__(self, host_map, names=None, visible=True, decimals=2, opened=True):
        from ipytree import Tree

        self.host_map = host_map
        self.names = names
        self.visible = visible
        self.decimals = decimals
        self.opened = opened

        host_map.default_style = {"cursor": "crosshair"}

        self.toolbar_button = widgets.ToggleButton(
            value=opened,
            tooltip="Inspector",
            icon="info",
            layout=widgets.Layout(width="28px", height="28px",
                                  padding="0px 0px 0px 4px"),
        )
        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            button_style="primary",
            layout=widgets.Layout(height="28px", width="28px",
                                  padding="0px 0px 0px 4px"),
        )
        self.inspector_output = widgets.Output(layout={
            "border": "1px solid black",
            "max_width": "600px",
            "max_height": "500px",
            "overflow": "auto",
        })
        expand_label = widgets.Label(
            "Expand   ",
            layout=widgets.Layout(padding="0px 0px 0px 4px"),
        )
        expand_point = widgets.Checkbox(
            description="Point",
            indent=False,
            value=self.expand_point,
            layout=widgets.Layout(width="65px"),
        )
        expand_pixels = widgets.Checkbox(
            description="Pixels",
            indent=False,
            value=self.expand_pixels,
            layout=widgets.Layout(width="65px"),
        )
        expand_objects = widgets.Checkbox(
            description="Objects",
            indent=False,
            value=self.expand_objects,
            layout=widgets.Layout(width="70px"),
        )
        self.inspector_checks = widgets.HBox(children=[
            expand_label,
            widgets.Label(""),
            expand_point,
            expand_pixels,
            expand_objects,
        ])
        self._clear_inspector_output()

        self.toolbar_header = widgets.HBox(children=[close_button, self.toolbar_button])
        self.toolbar_footer = widgets.VBox(children=[self.inspector_output])

        # Set up events.
        expand_point.observe(self._on_expand_point_changed, "value")
        expand_pixels.observe(self._on_expand_pixels_changed, "value")
        expand_objects.observe(self._on_expand_objects_changed, "value")
        self.toolbar_button.observe(self._on_toolbar_btn_click, "value")
        close_button.observe(self._on_close_btn_click, "value")

        # Set up map event.
        host_map.on_interaction(self._on_map_interaction)

        # TODO: Is this to trigger the on_opened behavior?
        self.toolbar_button.value = opened

        super().__init__(children=[self.toolbar_header, self.toolbar_footer])

    def _on_map_interaction(self, **kwargs):
        latlon = kwargs.get("coordinates")
        if kwargs.get("type") == "click" and self.toolbar_button.value:
            self.host_map.default_style = {"cursor": "wait"}
            self._clear_inspector_output()
            tree = Tree()
            nodes = []
            nodes.append(self._point_info(latlon, return_node=True))
            pixels_node = self._pixels_info(
                latlon, self.names, self.visible, self.decimals, return_node=True
            )
            if pixels_node.nodes:
                nodes.append(pixels_node)
            objects_node = self._objects_info(
                latlon, self.names, self.visible, return_node=True)
            if objects_node.nodes:
                nodes.append(objects_node)
            tree.nodes = nodes
            with self.inspector_output:
                display(tree)
            self.host_map.default_style = {"cursor": "crosshair"}

    def _clear_inspector_output(self):
        with self.inspector_output:
            self.inspector_output.clear_output(wait=True)
            display(self.inspector_checks)

    def _on_expand_point_changed(self, change):
        self.expand_point = change["new"]

    def _on_expand_pixels_changed(self, change):
        self.expand_pixels = change["new"]

    def _on_expand_objects_changed(self, change):
        self.expand_objects = change["new"]

    def _on_toolbar_btn_click(self, change):
        if change["new"]:
            self.host_map.default_style = {"cursor": "crosshair"}
            self.children = [self.toolbar_header, self.toolbar_footer]
            self._clear_inspector_output()
        else:
            self.children = [self.toolbar_button]
            self.host_map.default_style = {"cursor": "default"}

    def _on_close_btn_click(self, change):
        if change["new"]:
            self.host_map.default_style = {"cursor": "default"}
            self.toolbar_button.value = False
            if self.host_map is not None:
                self.host_map.toolbar_reset()
                self.host_map.on_interaction(self._on_map_interaction, remove=True)
                if (
                    self.host_map.inspector_control is not None
                    and self.host_map.inspector_control in self.host_map.controls
                ):
                    self.host_map.remove_control(self.host_map.inspector_control)
                    self.host_map.inspector_control = None
                    delattr(self.host_map, "inspector_control")
            self.close()

    def _point_info(self, latlon, decimals=3, return_node=False):
        from ipytree import Node, Tree

        scale = self.host_map.get_scale()
        point_nodes = [
            Node(f"Longitude: {latlon[1]}"),
            Node(f"Latitude: {latlon[0]}"),
            Node(f"Zoom Level: {self.host_map.zoom}"),
            Node(f"Scale (approx. m/px): {scale}"),
        ]
        label = f"Point ({latlon[1]:.{decimals}f}, {latlon[0]:.{decimals}f}) at {int(scale)}m/px"
        root_node = Node(
            label, nodes=point_nodes, icon="map", opened=self.expand_point
        )
        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"
        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])

    def _pixels_info(
        self, latlon, names=None, visible=True, decimals=2, return_node=False
    ):
        from ipytree import Node, Tree

        if names is not None:
            if isinstance(names, str):
                names = [names]
            layers = {}
            for name in names:
                if name in self.host_map.ee_layer_names:
                    layers[name] = self.host_map.ee_layer_dict[name]
        else:
            layers = self.host_map.ee_layer_dict
        xy = ee.Geometry.Point(latlon[::-1])
        sample_scale = self.host_map.getScale()

        nodes = []
        for layer in layers:
            layer_name = layer
            ee_object = layers[layer]["ee_object"]
            object_type = ee_object.__class__.__name__

            if visible and not self.host_map.ee_layer_dict[layer_name]["ee_layer"].visible:
                continue
            try:
                if isinstance(ee_object, ee.ImageCollection):
                    ee_object = ee_object.mosaic()

                if isinstance(ee_object, ee.Image):
                    item = ee_object.reduceRegion(
                        ee.Reducer.first(), xy, sample_scale
                    ).getInfo()
                    b_name = "band"
                    if len(item) > 1:
                        b_name = "bands"

                    label = f"{layer_name}: {object_type} ({len(item)} {b_name})"
                    layer_node = Node(label, opened=self.expand_pixels)

                    keys = sorted(item.keys())
                    for key in keys:
                        value = item[key]
                        if isinstance(value, float):
                            value = round(value, decimals)
                        layer_node.add_node(Node(f"{key}: {value}", icon="file"))

                    nodes.append(layer_node)
            except:
                pass

        root_node = Node("Pixels", icon="archive")
        root_node.nodes = nodes
        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"
        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])

    def _objects_info(self, latlon, names=None, visible=True, return_node=False):
        from ipytree import Node, Tree

        if names is not None:
            if isinstance(names, str):
                names = [names]
            layers = {}
            for name in names:
                if name in self.host_map.ee_layer_names:
                    layers[name] = self.host_map.ee_layer_dict[name]
        else:
            layers = self.host_map.ee_layer_dict

        xy = ee.Geometry.Point(latlon[::-1])

        nodes = []

        for layer in layers:
            layer_name = layer
            ee_object = layers[layer]["ee_object"]

            if visible:
                if not self.host_map.ee_layer_dict[layer_name]["ee_layer"].visible:
                    continue

            if isinstance(ee_object, ee.FeatureCollection):
                # Check geometry type
                geom_type = ee.Feature(ee_object.first()).geometry().type()
                lat, lon = latlon
                delta = 0.005
                bbox = ee.Geometry.BBox(
                    lon - delta,
                    lat - delta,
                    lon + delta,
                    lat + delta,
                )
                # Create a bounding box to filter points
                xy = ee.Algorithms.If(
                    geom_type.compareTo(ee.String("Point")),
                    xy,
                    bbox,
                )
                ee_object = ee_object.filterBounds(xy).first()
            try:
                nodes.append(get_info(
                    ee_object, layer_name, opened=self.expand_objects, return_node=True
                ))
            except:
                pass

        root_node = Node("Objects", icon="archive")
        root_node.nodes = nodes
        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"
        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])
