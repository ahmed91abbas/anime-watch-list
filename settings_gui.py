import tkinter as tk
from copy import deepcopy
from functools import partial
from tkinter import colorchooser

from gui_utils import GuiUtils


class SettingsGUI(GuiUtils):
    def __init__(self, caller_components_methods):
        super().__init__(__file__)
        self.caller_components_methods = caller_components_methods
        self.components_methods = {key: [] for key in self.theme_color_keys}
        self.create_gui()
        self.mainloop()

    def create_gui(self):
        sec_bg_color = self.get_color("secondary_background_color")
        text_color = self.get_color("text_color")
        font = ("calibri", 12)
        self.top = tk.Toplevel(bg=sec_bg_color)
        self.components_methods["secondary_background_color"].append((self.top.config, "bg"))
        self.add_icon(self.top)
        self.top.geometry(self.get_geometry())
        self.top.title("Settings")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.focus()

        self.header_frame = tk.Frame(self.top, bg=sec_bg_color)
        self.components_methods["secondary_background_color"].append((self.header_frame.config, "bg"))
        self.header_frame.pack(padx=20, pady=20)
        self.body_frame = tk.Frame(self.top, bg=sec_bg_color)
        self.components_methods["secondary_background_color"].append((self.body_frame.config, "bg"))
        self.body_frame.pack(padx=20, pady=20)

        self.theme_var = tk.StringVar(self.top)
        self.theme_var.set(self.get_current_theme())
        self.theme_var.trace_add("write", self.on_theme_change)
        theme_label = tk.Label(self.header_frame, text="Select theme: ", bg=sec_bg_color, fg=text_color, font=font)
        self.components_methods["secondary_background_color"].append((theme_label.config, "bg"))
        self.components_methods["text_color"].append((theme_label.config, "fg"))
        theme_dropdown = tk.OptionMenu(self.header_frame, self.theme_var, *self.get_available_themes())
        menu_config = {"bg": self.get_color("background_color"), "fg": text_color, "font": font}
        theme_dropdown.config(width=20, **menu_config)
        self.components_methods["background_color"].append((theme_dropdown.config, "bg"))
        self.components_methods["text_color"].append((theme_dropdown.config, "fg"))
        theme_dropdown["menu"].config(**menu_config)
        self.components_methods["background_color"].append((theme_dropdown["menu"].config, "bg"))
        self.components_methods["text_color"].append((theme_dropdown["menu"].config, "fg"))
        self.components_methods["background_color"].append((theme_dropdown["menu"].config, "bg"))
        self.components_methods["text_color"].append((theme_dropdown["menu"].config, "fg"))
        theme_dropdown.pack(side="right")
        theme_label.pack(side="right")

        padx = 5
        pady = 5
        button_config = {
            "width": 30,
            "height": 2,
            "font": font,
            "bg": self.get_color("button_color"),
            "fg": text_color,
        }
        display_config = {"width": 7, "height": 3, "relief": "solid"}
        for i, key in enumerate(self.theme_color_keys):
            color_display = tk.Label(self.body_frame, bg=self.get_color(key), **display_config)
            self.components_methods[key].append((color_display.config, "bg"))
            color_button = tk.Button(
                self.body_frame,
                text=f"Change {key.replace('_', ' ')}",
                command=partial(self.choose_color, key),
                **button_config,
            )
            self.components_methods["button_color"].append((color_button.config, "bg"))
            self.components_methods["text_color"].append((color_button.config, "fg"))
            color_button.grid(row=i, column=0, padx=padx, pady=pady)
            color_display.grid(row=i, column=1, padx=padx, pady=pady)

    def choose_color(self, color_key):
        _, color_code = colorchooser.askcolor(title=f"Choose {color_key.replace('_', ' ')}")
        if not color_code:
            return
        for method, arg_key in self.caller_components_methods[color_key] + self.components_methods[color_key]:
            method(**{arg_key: color_code})
        current_colors = deepcopy(self.themes_config["themes"][self.current_theme])
        current_colors[color_key] = color_code
        self.set_current_theme("custom")
        for key, color in current_colors.items():
            self.set_color(color, key)
        self.theme_var.set("custom")

    def on_theme_change(self, *args):
        selected_theme = self.theme_var.get()
        self.set_current_theme(selected_theme)
        for key in self.theme_color_keys:
            color = self.get_color(key)
            for method, arg_key in self.caller_components_methods[key] + self.components_methods[key]:
                method(**{arg_key: color})

    def on_close(self):
        self.set_geometry(self.top.geometry())
        self.top.destroy()

    def mainloop(self):
        tk.mainloop()


if __name__ == "__main__":
    SettingsGUI()
