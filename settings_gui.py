import tkinter as tk
from tkinter import colorchooser

from gui_utils import GuiUtils


class SettingsGUI(GuiUtils):
    def __init__(self, caller):
        defaults = {"background_color": "#e6e6ff"}
        super().__init__(__file__, defaults)
        self.background_color = None
        self.caller = caller
        self.create_gui()
        self.mainloop()

    def create_gui(self):
        bg_color = self.get_bg_color()
        title_font = ("calibri", 16)
        self.top = tk.Toplevel(bg=bg_color)
        self.top.geometry(self.get_geometry())
        self.top.title("Settings")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.focus()

        self.header_frame = tk.Frame(self.top, bg=bg_color)
        self.body_frame = tk.Frame(self.top, bg=bg_color)
        self.header_frame.pack()
        self.body_frame.pack()

        self.title_text = tk.Text(self.header_frame, wrap="word", height=2, bd=0, font=title_font, bg=bg_color)
        self.replace_widget_text(self.title_text, "Anime Watch List Settings")
        self.title_text.pack(pady=10)

        pady = 15
        tk.Button(self.body_frame, text="Change background color", command=self.choose_bg_color).pack(pady=pady)
        tk.Button(
            self.body_frame, text="Change secondary background color", command=self.choose_secondary_bg_color
        ).pack(pady=pady)
        tk.Button(self.body_frame, text="Change button color", command=self.choose_button_color).pack(pady=pady)
        tk.Button(self.body_frame, text="Apply", command=self.on_apply).pack(pady=pady)

    def choose_bg_color(self):
        _, color_code = colorchooser.askcolor(title="Choose background color")
        if color_code:
            self.caller.set_bg_color(color_code)
            for method, key in self.caller.components_methods["background_color"]:
                method(**{key: color_code})

    def choose_secondary_bg_color(self):
        _, color_code = colorchooser.askcolor(title="Choose secondary background color")
        if color_code:
            self.caller.set_secondary_bg_color(color_code)
            for method, key in self.caller.components_methods["secondary_background_color"]:
                method(**{key: color_code})

    def choose_button_color(self):
        _, color_code = colorchooser.askcolor(title="Choose button color")
        if color_code:
            self.caller.set_button_color(color_code)
            for method, key in self.caller.components_methods["button_color"]:
                method(**{key: color_code})

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
