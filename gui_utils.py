import json
import os

from screeninfo import get_monitors


class GuiUtils:
    def __init__(self, filepath):
        self.filepath = filepath
        self.settings = None

    def load_settings(func):
        def wrapper(self, *args, **kwargs):
            self.settings = self.settings if self.settings else self.read_settings()
            return func(self, *args, **kwargs)

        return wrapper

    def read_settings(self):
        with open(self.filepath, "r") as f:
            return json.load(f)

    def save_settings(self):
        with open(self.filepath, "w") as f:
            json.dump(self.settings, f, indent=4)

    @load_settings
    def get_geometry(self):
        monitors = get_monitors()
        geometry = "+400+250"
        if "geometry" in self.settings and any(
            [int(self.settings["geometry"].split("+")[1]) < m.x + m.width for m in monitors]
        ):
            geometry = self.settings["geometry"]
        else:
            for m in monitors:
                if m.is_primary:
                    geometry = f"+{m.width // 4}+{m.height // 4}"
        self.settings["geometry"] = geometry
        return geometry
