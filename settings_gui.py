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
        color_button = tk.Button(self.body_frame, text="Change background color", command=self.choose_bg_color)
        color_button.pack(pady=pady)
        apply_button = tk.Button(self.body_frame, text="Apply", command=self.on_apply)
        apply_button.pack(pady=pady)

    def choose_bg_color(self):
        _, self.background_color = colorchooser.askcolor(title="Choose background color")

    def on_apply(self):
        if self.background_color:
            self.caller.set_bg_color(self.background_color)
            for method, key in self.caller.components_methods["background_color"]:
                method(**{key: self.background_color})

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
