import tkinter as tk
from tkinter import colorchooser

from gui_utils import GuiUtils


class SettingsGUI(GuiUtils):
    def __init__(self, caller):
        defaults = {"background_color": "#e6e6ff", "button_color": "#f7e4d0"}
        super().__init__(__file__, defaults)
        self.background_color = None
        self.caller = caller
        self.create_gui()
        self.mainloop()

    def create_gui(self):
        bg_color = self.get_bg_color()
        self.top = tk.Toplevel(bg=bg_color)
        self.add_icon(self.top)
        self.top.geometry(self.get_geometry())
        self.top.title("Settings")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.focus()

        self.body_frame = tk.Frame(self.top, bg=bg_color)
        self.body_frame.pack(padx=20, pady=20)

        padx = 5
        pady = 5
        button_config = {"width": 30, "height": 2, "font": ("calibri", 12), "bg": self.get_button_color()}
        display_config = {"width": 7, "height": 3, "relief": "solid"}
        bg_color_button = tk.Button(
            self.body_frame, text="Change background color", command=self.choose_bg_color, **button_config
        )
        bg_color_button.grid(row=0, column=0, padx=padx, pady=pady)
        self.bg_color_display = tk.Label(self.body_frame, bg=self.caller.get_bg_color(), **display_config)
        self.bg_color_display.grid(row=0, column=1, padx=padx, pady=pady)
        sec_bg_color_button = tk.Button(
            self.body_frame,
            text="Change secondary background color",
            command=self.choose_secondary_bg_color,
            **button_config
        )
        sec_bg_color_button.grid(row=1, column=0, padx=padx, pady=pady)
        self.sec_bg_color_display = tk.Label(
            self.body_frame, bg=self.caller.get_secondary_bg_color(), **display_config
        )
        self.sec_bg_color_display.grid(row=1, column=1, padx=padx, pady=pady)
        button_color_button = tk.Button(
            self.body_frame, text="Change button color", command=self.choose_button_color, **button_config
        )
        button_color_button.grid(row=2, column=0, padx=padx, pady=pady)
        self.button_color_display = tk.Label(self.body_frame, bg=self.caller.get_button_color(), **display_config)
        self.button_color_display.grid(row=2, column=1, padx=padx, pady=pady)

    def choose_bg_color(self):
        _, color_code = colorchooser.askcolor(title="Choose background color")
        if color_code:
            for method, key in self.caller.components_methods["background_color"]:
                method(**{key: color_code})
            self.bg_color_display.config(bg=color_code)
            self.caller.set_bg_color(color_code)

    def choose_secondary_bg_color(self):
        _, color_code = colorchooser.askcolor(title="Choose secondary background color")
        if color_code:
            for method, key in self.caller.components_methods["secondary_background_color"]:
                method(**{key: color_code})
            self.sec_bg_color_display.config(bg=color_code)
            self.caller.set_secondary_bg_color(color_code)

    def choose_button_color(self):
        _, color_code = colorchooser.askcolor(title="Choose button color")
        if color_code:
            for method, key in self.caller.components_methods["button_color"]:
                method(**{key: color_code})
            self.button_color_display.config(bg=color_code)
            self.caller.set_button_color(color_code)

    def on_apply(self):
        pass

    def on_close(self):
        self.set_geometry(self.top.geometry())
        self.top.destroy()

    def mainloop(self):
        tk.mainloop()

    def replace_widget_text(self, text_widget, text):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", text)
        text_widget.tag_configure("center", justify="center")
        text_widget.tag_add("center", "1.0", "end")
        text_widget.config(state=tk.DISABLED)


if __name__ == "__main__":
    SettingsGUI()
