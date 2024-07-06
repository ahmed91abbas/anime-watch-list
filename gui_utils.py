import base64
import io
import json
import os
from copy import deepcopy

from PIL import Image, ImageTk
from screeninfo import get_monitors


class GuiUtils:
    def __init__(self, filepath):
        self.settings_filepath = os.path.join("configs", f"{os.path.splitext(os.path.basename(filepath))[0]}.json")
        self.settings = {}
        self.defaults = {
            "background_color": "#e6e6ff",
            "secondary_background_color": "#b28fc7",
            "button_color": "#f7e4d0",
            "max_rows": 8,
        }

    def reset_settings(self):
        if os.path.exists(self.settings_filepath):
            os.remove(self.settings_filepath)
        self.settings = deepcopy(self.defaults)

    def load_settings(func):
        def wrapper(self, *args, **kwargs):
            self.settings = self.settings if self.settings else self.read_settings()
            self.settings = {**self.defaults, **self.settings}
            return func(self, *args, **kwargs)

        return wrapper

    def persist_settings(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.save_settings()

        return wrapper

    def read_settings(self):
        if not os.path.exists(self.settings_filepath):
            return {}
        with open(self.settings_filepath, "r") as f:
            return json.load(f)

    def save_settings(self):
        with open(self.settings_filepath, "w") as f:
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

    @persist_settings
    def set_geometry(self, root_geometry):
        self.settings["geometry"] = root_geometry[root_geometry.index("+") :]

    @load_settings
    def get_bg_color(self):
        return self.settings["background_color"]

    @persist_settings
    def set_bg_color(self, background_color):
        self.settings["background_color"] = background_color

    @load_settings
    def get_secondary_bg_color(self):
        return self.settings["secondary_background_color"]

    @persist_settings
    def set_secondary_bg_color(self, secondary_background_color):
        self.settings["secondary_background_color"] = secondary_background_color

    @load_settings
    def get_button_color(self):
        return self.settings["button_color"]

    @persist_settings
    def set_button_color(self, button_color):
        self.settings["button_color"] = button_color

    @load_settings
    def get_max_rows(self):
        return self.settings["max_rows"]

    @persist_settings
    def set_max_rows(self, max_rows):
        self.settings["max_rows"] = max_rows

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
