import base64
import io
import json
import os
from copy import deepcopy

from PIL import Image, ImageTk
from screeninfo import get_monitors


class GuiUtils:
    def __init__(self, filepath, defaults={}):
        self.settings_filepath = os.path.join("configs", f"{os.path.splitext(os.path.basename(filepath))[0]}.json")
        self.themes_filepath = os.path.join("configs", "themes.json")
        self.settings = {}
        self.themes_config = {}
        self.default_themes_config = {
            "current": "default",
            "themes": {
                "default": {
                    "background_color": "#e6e6ff",
                    "secondary_background_color": "#b28fc7",
                    "button_color": "#f7e4d0",
                    "text_color": "#000000",
                },
                "dark": {
                    "background_color": "#676767",
                    "secondary_background_color": "#000000",
                    "button_color": "#414141",
                    "text_color": "#ffffff",
                },
            },
        }
        self.theme_color_keys = list(self.default_themes_config["themes"]["default"].keys())
        self.current_theme = "default"
        self.defaults = defaults

    def restore_defaults(self):
        if os.path.exists(self.settings_filepath):
            os.remove(self.settings_filepath)
        self.settings = deepcopy(self.defaults)

    def load_settings(func):
        def wrapper(self, *args, **kwargs):
            self.settings = self.settings if self.settings else self.read_json_file(self.settings_filepath)
            self.settings = {**self.defaults, **self.settings}
            return func(self, *args, **kwargs)

        return wrapper

    def persist_settings(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.save_json(self.settings_filepath, self.settings)

        return wrapper

    def load_themes(func):
        def wrapper(self, *args, **kwargs):
            self.themes_config = (
                self.themes_config if self.themes_config else self.read_json_file(self.themes_filepath)
            )
            if not self.themes_config:
                self.themes_config = deepcopy(self.default_themes_config)
            self.current_theme = self.themes_config["current"]
            return func(self, *args, **kwargs)

        return wrapper

    def persist_themes(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.save_json(self.themes_filepath, self.themes_config)

        return wrapper

    def read_json_file(self, filepath):
        if not os.path.exists(filepath):
            return {}
        with open(filepath, "r") as f:
            return json.load(f)

    def save_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

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

    @persist_settings
    def set_geometry(self, root_geometry):
        self.settings["geometry"] = root_geometry[root_geometry.index("+") :]

    @load_themes
    def get_color(self, key):
        return self.themes_config["themes"][self.current_theme][key]

    @persist_themes
    def set_color(self, background_color, key):
        self.themes_config["themes"][self.current_theme][key] = background_color

    @load_settings
    def get_max_rows(self):
        return self.settings["max_rows"]

    @persist_settings
    def set_max_rows(self, max_rows):
        self.settings["max_rows"] = max_rows

    @load_themes
    def get_current_theme(self):
        return self.current_theme

    @load_themes
    def get_available_themes(self):
        return list(self.themes_config["themes"].keys())

    @persist_themes
    def set_current_theme(self, theme_name):
        if theme_name not in self.themes_config["themes"]:
            self.themes_config["themes"][theme_name] = {}
        for key in self.theme_color_keys:
            if key not in self.themes_config["themes"][theme_name]:
                self.themes_config["themes"][theme_name][key] = self.get_color(key)
        self.current_theme = theme_name
        self.themes_config["current"] = theme_name

    def add_icon(self, root):
        icon_img = ImageTk.PhotoImage(file=os.path.join("images", "icon.ico"))
        root.tk.call("wm", "iconphoto", root._w, icon_img)

    def get_image_data(self, base64_image_data, width, height):
        image_data = base64.b64decode(base64_image_data)
        img = Image.open(io.BytesIO(image_data))
        img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def trim_text(self, text, max_length):
        if len(text) > max_length:
            return f"{text[:max_length-3].rstrip()}..."
        return text
