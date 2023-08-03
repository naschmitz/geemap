"""Various ipywidgets that can be added to a map."""

import ipywidgets

from IPython.core.display import display
import ee
import ipytree
from . import common


class Colorbar(ipywidgets.Output):
    """A matplotlib colorbar widget that can be added to the map."""

    def __init__(
        self,
        vis_params=None,
        cmap="gray",
        discrete=False,
        label=None,
        orientation="horizontal",
        transparent_bg=False,
        font_size=9,
        axis_off=False,
        max_width=None,
        **kwargs,
    ):
        """Add a matplotlib colorbar to the map.

        Args:
            vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
            discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
            transparent_bg (bool, optional): Whether to use transparent background. Defaults to False.
            font_size (int, optional): Font size for the colorbar. Defaults to 9.
            axis_off (bool, optional): Whether to turn off the axis. Defaults to False.
            max_width (str, optional): Maximum width of the colorbar in pixels. Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not scalar type.
            ValueError: If the provided max value is not scalar type.
            ValueError: If the provided opacity value is not scalar type.
            ValueError: If cmap or palette is not provided.
        """

        import matplotlib  # pylint: disable=import-outside-toplevel
        import numpy  # pylint: disable=import-outside-toplevel

        if max_width is None:
            if orientation == "horizontal":
                max_width = "270px"
            else:
                max_width = "100px"

        if isinstance(vis_params, (list, tuple)):
            vis_params = {"palette": list(vis_params)}
        elif not vis_params:
            vis_params = {}

        if not isinstance(vis_params, dict):
            raise TypeError("The vis_params must be a dictionary.")

        if isinstance(kwargs.get("colors"), (list, tuple)):
            vis_params["palette"] = list(kwargs["colors"])

        width, height = self._get_dimensions(orientation, kwargs)

        vmin = vis_params.get("min", kwargs.pop("vmin", 0))
        if type(vmin) not in (int, float):
            raise TypeError("The provided min value must be scalar type.")

        vmax = vis_params.get("max", kwargs.pop("mvax", 1))
        if type(vmax) not in (int, float):
            raise TypeError("The provided max value must be scalar type.")

        alpha = vis_params.get("opacity", kwargs.pop("alpha", 1))
        if type(alpha) not in (int, float):
            raise TypeError("The provided opacity or alpha value must be type scalar.")

        if "palette" in vis_params.keys():
            hexcodes = common.to_hex_colors(common.check_cmap(vis_params["palette"]))
            if discrete:
                cmap = matplotlib.colors.ListedColormap(hexcodes)
                linspace = numpy.linspace(vmin, vmax, cmap.N + 1)
                norm = matplotlib.colors.BoundaryNorm(linspace, cmap.N)
            else:
                cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
                    "custom", hexcodes, N=256
                )
                norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        elif cmap:
            cmap = matplotlib.pyplot.get_cmap(cmap)
            norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        else:
            raise ValueError(
                'cmap keyword or "palette" key in vis_params must be provided.'
            )

        fig, ax = matplotlib.pyplot.subplots(figsize=(width, height))
        cb = matplotlib.colorbar.ColorbarBase(
            ax,
            norm=norm,
            alpha=alpha,
            cmap=cmap,
            orientation=orientation,
            **kwargs,
        )

        label = label or vis_params.get("bands") or kwargs.pop("caption", None)
        if label:
            cb.set_label(label, fontsize=font_size)

        if axis_off:
            ax.set_axis_off()
        ax.tick_params(labelsize=font_size)

        # Set the background color to transparent.
        if transparent_bg:
            fig.patch.set_alpha(0.0)

        super().__init__(layout=ipywidgets.Layout(width=max_width))
        with self:
            self.outputs = ()
            matplotlib.pyplot.show()

    def _get_dimensions(self, orientation, kwargs):
        default_dims = {"horizontal": (3.0, 0.3), "vertical": (0.3, 3.0)}
        if orientation in default_dims:
            default = default_dims[orientation]
            return (
                kwargs.get("width", default[0]),
                kwargs.get("height", default[1]),
            )
        raise ValueError(
            f"orientation must be one of [{', '.join(default_dims.keys())}]."
        )


class Inspector(ipywidgets.VBox):
    host_map = None
    expand_point = False
    expand_pixels = True
    expand_objects = False
    on_close = None

    def __init__(self, host_map, names=None, visible=True, decimals=2, opened=True):
        self.host_map = host_map
        self.names = names
        self.visible = visible
        self.decimals = decimals
        self.opened = opened

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

        self.inspector_output = ipywidgets.Output(
            layout=ipywidgets.Layout(
                max_width="600px", max_height="500px", overflow="auto"
            )
        )
        expand_point = self._create_expand_checkbox("Point", self.expand_point)
        expand_pixels = self._create_expand_checkbox("Pixels", self.expand_pixels)
        expand_objects = self._create_expand_checkbox("Objects", self.expand_objects)
        expand_point.observe(self._on_expand_point_changed, "value")
        expand_pixels.observe(self._on_expand_pixels_changed, "value")
        expand_objects.observe(self._on_expand_objects_changed, "value")
        self.inspector_checks = ipywidgets.HBox(
            children=[
                ipywidgets.Label(
                    "Expand", layout=ipywidgets.Layout(padding="0px 8px 0px 4px")
                ),
                expand_point,
                expand_pixels,
                expand_objects,
            ]
        )
        self._clear_inspector_output()

        self.toolbar_header = ipywidgets.HBox(
            children=[close_button, self.toolbar_button]
        )
        self.toolbar_footer = ipywidgets.VBox(children=[self.inspector_output])

        host_map.on_interaction(self._on_map_interaction)
        self.toolbar_button.value = opened

        super().__init__(children=[self.toolbar_header, self.toolbar_footer])

    def _create_expand_checkbox(self, title, checked):
        layout = ipywidgets.Layout(width="auto", padding="0px 6px 0px 0px")
        return ipywidgets.Checkbox(
            description=title, indent=False, value=checked, layout=layout
        )

    def _on_map_interaction(self, **kwargs):
        latlon = kwargs.get("coordinates")
        if kwargs.get("type") == "click" and self.toolbar_button.value:
            self.host_map.default_style = {"cursor": "wait"}
            self._clear_inspector_output()
            tree = ipytree.Tree()
            nodes = []
            nodes.append(self._point_info(latlon, return_node=True))
            pixels_node = self._pixels_info(latlon, return_node=True)
            if pixels_node.nodes:
                nodes.append(pixels_node)
            objects_node = self._objects_info(latlon, return_node=True)
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
            if self.host_map:
                self.host_map.default_style = {"cursor": "default"}
                self.host_map.on_interaction(self._on_map_interaction, remove=True)
            if self.on_close is not None:
                self.on_close()

    def _get_visible_map_layers(self):
        layers = {}
        if self.names:
            names = [names] if isinstance(names, str) else self.names
            for name in names:
                if name in self.host_map.ee_layer_names:
                    layers[name] = self.host_map.ee_layer_dict[name]
        else:
            layers = self.host_map.ee_layer_dict
        return {k: v for k, v in layers.items() if v["ee_layer"].visible}

    def _root_node(self, title, nodes, return_node, **kwargs):
        root_node = ipytree.Node(
            title,
            icon="archive",
            nodes=nodes,
            open_icon="plus-square",
            open_icon_style="success",
            close_icon="minus-square",
            close_icon_style="info",
            **kwargs,
        )
        return root_node if return_node else ipytree.Tree(nodes=[root_node])

    def _point_info(self, latlon, return_node=False):
        scale = self.host_map.get_scale()
        label = f"Point ({latlon[1]:.{self.decimals}f}, {latlon[0]:.{self.decimals}f}) at {int(scale)}m/px"
        nodes = [
            ipytree.Node(f"Longitude: {latlon[1]}"),
            ipytree.Node(f"Latitude: {latlon[0]}"),
            ipytree.Node(f"Zoom Level: {self.host_map.zoom}"),
            ipytree.Node(f"Scale (approx. m/px): {scale}"),
        ]
        return self._root_node(label, nodes, return_node, opened=self.expand_point)

    def _pixels_info(self, latlon, return_node=False):
        if not self.visible:
            return self._root_node("Pixels", [], return_node)

        layers = self._get_visible_map_layers()
        xy = ee.Geometry.Point(latlon[::-1])
        scale = self.host_map.getScale()
        nodes = []
        for layer_name, layer in layers.items():
            obj = layer["ee_object"]
            if isinstance(obj, ee.ImageCollection):
                obj = obj.mosaic()
            if isinstance(obj, ee.Image):
                try:
                    item = obj.reduceRegion(ee.Reducer.first(), xy, scale).getInfo()
                except:
                    continue
                b_name = "band" if len(item) == 1 else "bands"
                obj_type = obj.__class__.__name__
                label = f"{layer_name}: {obj_type} ({len(item)} {b_name})"
                layer_node = ipytree.Node(label, opened=self.expand_pixels)
                for key, value in sorted(item.items()):
                    if isinstance(value, float):
                        value = round(value, self.decimals)
                    layer_node.add_node(ipytree.Node(f"{key}: {value}", icon="file"))
                nodes.append(layer_node)

        return self._root_node("Pixels", nodes, return_node)

    def _objects_info(self, latlon, return_node=False):
        if not self.visible:
            return self._root_node("Objects", [], return_node)

        layers = self._get_visible_map_layers()
        xy = ee.Geometry.Point(latlon[::-1])
        nodes = []
        for layer_name, layer in layers.items():
            obj = layer["ee_object"]
            if isinstance(obj, ee.FeatureCollection):
                geom_type = ee.Feature(obj.first()).geometry().type()
                lat, lon = latlon
                delta = 0.005
                bbox = ee.Geometry.BBox(
                    lon - delta, lat - delta, lon + delta, lat + delta
                )
                xy = ee.Algorithms.If(geom_type.compareTo(ee.String("Point")), xy, bbox)
                obj = obj.filterBounds(xy).first()
            try:
                nodes.append(
                    common.get_info(
                        obj, layer_name, opened=self.expand_objects, return_node=True
                    )
                )
            except:
                pass

        return self._root_node("Objects", nodes, return_node)
