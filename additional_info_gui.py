import io
import base64
import webbrowser
import tkinter as tk
from PIL import Image, ImageTk
from threading import Thread
from config_generator import ConfigGenerator

class AdditionalInfoGUI():
    def __init__(self, title, base64_image_data):
        self.generator = ConfigGenerator()
        self.title = title
        raw_image_data = base64.b64decode(base64_image_data)
        labels = self.create_gui(raw_image_data)
        Thread(target=self.update_gui, args=(labels, )).start()
        self.mainloop()

    def create_gui(self, raw_image_data):
        self.bg_color = '#e6e6ff'
        title_font = ('calibri', 16)
        self.top = tk.Toplevel(bg=self.bg_color)
        self.top.title("Additional information")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)

        self.headerFrame = tk.Frame(self.top, bg=self.bg_color)
        bodyFrame = tk.Frame(self.top, bg=self.bg_color)
        self.headerFrame.pack()
        bodyFrame.pack()

        tk.Label(self.headerFrame, text=self.title, bg=self.bg_color, font=title_font).pack(pady=10)

        padx = 15
        pady = 15
        image = self.get_image_data(raw_image_data, 320, 500)
        img_label = tk.Label(bodyFrame, bg=self.bg_color, image=image)
        img_label.image = image
        img_label.pack(side=tk.LEFT, padx=padx, pady=pady)

        self.info_frame = tk.Frame(bodyFrame, bg=self.bg_color)
        self.info_frame.pack(side=tk.TOP, padx=padx, pady=pady)
        info = self.generator.get_skeleton_additional_info()
        first_column_width = max([len(key) for key in info.keys()]) + 2
        second_column_width = 40
        label_config = {'bg': self.bg_color, 'font': ('calibri', 13), 'borderwidth': 2, 'relief': 'groove'}
        label_grid_config = {'sticky': 'w'}
        labels = list()
        for i, (k, v) in enumerate(info.items()):
            label1 = tk.Label(self.info_frame, text=k.capitalize(), width=first_column_width, **label_config)
            label1.grid(row=i, column=0, **label_grid_config)
            label2 = tk.Label(self.info_frame, text=v, width=second_column_width, **label_config)
            label2.grid(row=i, column=1, **label_grid_config)
            labels.append((label1, label2))
        return labels

    def update_gui(self, labels):
        self.top.title("Additional information (Loading...)")
        info = self.generator.get_additional_info(self.title)
        for label1, label2 in labels:
            key = label1.cget('text').lower()
            if key in info:
                label2.config(text=self.trim_text(str(info[key]), 40))
                if key == 'url':
                    url = info[key]
                    label2.bind("<Button-1>", lambda e: webbrowser.open(url, new=0, autoraise=True))
                    label2.config(fg='blue')
        self.top.title("Additional information")

    def get_image_data(self, image_raw_data, width, height):
        img = Image.open(io.BytesIO(image_raw_data))
        img = img.resize((width,height), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)

    def on_close(self):
        self.top.destroy()

    def trim_text(self, text, max_length):
        if len(text) > max_length:
            return f'{text[:max_length-3].rstrip()}...'
        return text

    def mainloop(self):
        tk.mainloop()
