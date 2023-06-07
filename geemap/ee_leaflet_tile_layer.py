import box
import geemap
import ee
import ipyleaflet


class EeLeafletTileLayer(ipyleaflet.TileLayer):
    """An ipyleaflet TileLayer that shows an EE object."""

    def __init__(self, ee_object, vis_params={}, name="Layer untitled", shown=True, opacity=1.0):
        """Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """

        image = self._ee_object_to_image(ee_object, vis_params)
        if "palette" in vis_params:
            vis_params["palette"] = self._validate_palette(vis_params)

        map_id_dict = ee.Image(image).getMapId(vis_params)
        super().__init__(
            url=map_id_dict["tile_fetcher"].url_format,
            attribution="Google Earth Engine",
            name=name,
            opacity=opacity,
            visible=shown,
        )

    def _ee_object_to_image(self, ee_object, vis_params):
        if isinstance(ee_object, (ee.Geometry, ee.Feature, ee.FeatureCollection)):
            color = vis_params.get("color", "000000")
            features = ee.FeatureCollection(ee_object)
            image_fill = features.style(**{"fillColor": color}).updateMask(
                ee.Image.constant(0.5)
            )
            width = vis_params.get("width", 2)
            image_outline = features.style(
                **{"color": color, "fillColor": "00000000", "width": width}
            )
            return image_fill.blend(image_outline)
        elif isinstance(ee_object, ee.Image):
            return ee_object
        elif isinstance(ee_object, ee.ImageCollection):
            return ee_object.mosaic()
        raise AttributeError(
            f"\n\nCannot add an object of type {ee_object.__class__.__name__} to the map.")

    def _validate_palette(self, vis_params):
        palette = vis_params["palette"]
        if isinstance(palette, box.Box):
            if "default" not in palette:
                raise ValueError("The provided palette Box object is invalid.")
            return palette["default"]
        elif isinstance(palette, str):
            return geemap.common.check_cmap(palette)
        elif isinstance(palette, list):
            return palette
        raise ValueError(
            "The palette must be a list of colors, a string, or a Box object."
        )
