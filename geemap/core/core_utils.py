import math


def get_scale(latlon, zoom):
    """Returns the pixel scale at the specified latlon and zoom in meters."""

    # Reference:
    # - https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
    # - https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale
    center_lat = latlon[0]
    center_lat_cos = math.cos(math.radians(center_lat))
    return 156543.04 * center_lat_cos / math.pow(2, zoom)
