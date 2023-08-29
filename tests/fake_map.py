class FakeMap:
    """A fake map used for initializing widgets."""

    def __init__(self):
        self.default_style = {}
        self.interaction_handlers = set()
        self.scale = 1024
        self.zoom = 7
        self.layers = []
        self.ee_layers = {}
        self.geojson_layers = []

        self._recognized_attrs = self.__dict__.keys()

    def __setattr__(self, k, v):
        if hasattr(self, "_recognized_attrs") and k not in self._recognized_attrs:
            raise AttributeError(f"{k} is not a recognized attr")
        super(FakeMap, self).__setattr__(k, v)

    def on_interaction(self, func, remove=False):
        if remove:
            if func in self.interaction_handlers:
                self.interaction_handlers.remove(func)
            else:
                raise ValueError("Removing an unknown on_interaction func.")
        else:
            if func in self.interaction_handlers:
                raise ValueError("This on_interaction func already exists.")
            else:
                self.interaction_handlers.add(func)

    def click(self, coordinates, event_type):
        for handler in self.interaction_handlers:
            handler(coordinates=coordinates, type=event_type)

    @property
    def cursor_style(self):
        return self.default_style.get("cursor")


class FakeEeTileLayer:
    def __init__(self, name="test-layer", visible=True, opacity=1.0):
        self.name = name
        self.visible = visible
        self.opacity = opacity


class FakeTileLayer:
    def __init__(self, name="test-layer", visible=True, opacity=1.0):
        self.name = name
        self.visible = visible
        self.opacity = opacity


class FakeGeoJSONLayer:
    def __init__(self, name="test-layer", visible=True, style=None):
        self.name = name
        self.visible = visible
        self.style = style or {}
