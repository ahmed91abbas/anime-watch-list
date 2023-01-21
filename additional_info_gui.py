import os
import tkinter as tk
import webbrowser
from threading import Thread

from config_generator import ConfigGenerator
from gui_utils import GuiUtils


class AdditionalInfoGUI(GuiUtils):
    def __init__(self, title, base64_image_data):
        setting_filepath = os.path.join("configs", os.path.basename(__file__).replace(".py", ".json"))
        super().__init__(setting_filepath)
        self.generator = ConfigGenerator()
        self.title = title
        self.base64_image_data = base64_image_data
        self.info_titles = [
            "Url",
            "Source",
            "Status",
            "Episodes",
            "Aired",
            "Score",
            "Season",
            "Genres",
            "Broadcast",
        ]
        self.create_gui()
        Thread(target=self.update_gui).start()
        self.mainloop()

    def create_gui(self):
        bg_color = "#e6e6ff"
        title_font = ("calibri", 16)
        self.top = tk.Toplevel(bg=bg_color)
        self.top.geometry(self.get_geometry())
        self.top.title("Additional information")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.focus()

        header_frame = tk.Frame(self.top, bg=bg_color)
        body_frame = tk.Frame(self.top, bg=bg_color)
        header_frame.pack()
        body_frame.pack()

        self.title_label = tk.Label(header_frame, text=f"{self.title}\n-", bg=bg_color, font=title_font)
        self.title_label.pack(pady=10)

        padx = 15
        pady = 15
        image = self.get_image_data(self.base64_image_data, 320, 500)
        img_label = tk.Label(body_frame, bg=bg_color, image=image)
        img_label.image = image
        img_label.pack(side=tk.LEFT, padx=padx, pady=pady)

        info_frame = tk.Frame(body_frame, bg=bg_color)
        info_frame.pack(side=tk.RIGHT, padx=(0, padx), pady=pady, fill=tk.BOTH)
        info_table_frame = tk.Frame(info_frame, bg=bg_color)
        info_table_frame.pack(side=tk.TOP)
        info_free_text_frame = tk.Frame(info_frame, bg=bg_color)
        info_free_text_frame.pack(side=tk.TOP, pady=(20, 0))

        first_column_width = max([len(title) for title in self.info_titles]) + 2
        second_column_width = 40
        label_config = {"bg": bg_color, "font": ("calibri", 13), "borderwidth": 2, "relief": "groove"}
        label_grid_config = {"sticky": "w"}
        self.labels_dict = dict()
        for i, info_title in enumerate(self.info_titles):
            label1 = tk.Label(info_table_frame, text=info_title, width=first_column_width, **label_config)
            label1.grid(row=i, column=0, **label_grid_config)
            label2 = tk.Label(info_table_frame, text="-", width=second_column_width, **label_config)
            label2.grid(row=i, column=1, **label_grid_config)
            self.labels_dict[info_title] = label2

        height = 20 - len(self.info_titles)
        width = first_column_width + second_column_width
        self.synopsis_text_widget = tk.Text(
            info_free_text_frame,
            font=label_config["font"],
            wrap="word",
            width=width,
            height=height,
            bg=bg_color,
            highlightthickness=0,
            borderwidth=0,
        )
        self.synopsis_text_widget.pack()

    def update_gui(self):
        self.add_icon(self.top)
        self.top.title("Additional information (Loading...)")
        info = self.generator.get_additional_info(self.title)
        self.title_label["text"] = f'{self.title}\n({info.get("title_english", "-")})'
        for info_title in self.info_titles:
            label = self.labels_dict[info_title]
            value = str(info.get(info_title.lower(), "-"))
            label.config(text=self.trim_text(value, 40))
            if info_title == "Url":
                url = value
                label.bind("<Button-1>", lambda e: webbrowser.open(url, new=0, autoraise=True))
                label.config(fg="blue")
        self.synopsis_text_widget.insert(tk.INSERT, info.get("synopsis", "-"))
        self.synopsis_text_widget.config(state=tk.DISABLED)
        self.top.title("Additional information")

    def on_close(self):
        geometry = self.top.geometry()
        self.settings["geometry"] = geometry[geometry.index("+") :]
        self.save_settings()
        self.top.destroy()

    def mainloop(self):
        tk.mainloop()
