import sys
import os
import io
import subprocess
import webbrowser
import tkinter as tk
from PIL import Image, ImageTk
from urllib.request import Request, urlopen
from functools import partial
from config_generator import ConfigGenerator
from threading import Thread


class AnimeWatchListGUI:
    def __init__(self):
        self.generator = ConfigGenerator()
        self.run()

    def run(self):
        elements = self.create_gui(self.generator.get_skeleton_config())
        Thread(target=self.add_config_to_gui, args=(elements, )).start()
        self.mainloop()

    def add_config_to_gui(self, elements):
        self.config = self.generator.get_config()
        self.config = self.sort_config(self.config)
        self.update_gui(self.config, elements)

    def sort_config(self, config):
        config = sorted(config, key=lambda x: x['title'])
        l1 = sorted(filter(lambda x: x['next_ep_url'], config), key=lambda x: float(x['ep'].replace('-', '.')), reverse=True)
        l2 = list(filter(lambda x: not x['next_ep_url'], config))
        return l1 + l2

    def create_gui(self, config, max_row_count=8):
        bg_color = '#e6e6ff'
        secondary_color = '#b28fc7'
        button_color = '#f7e4d0'

        self.root = tk.Tk()
        self.root.configure(background=secondary_color)
        self.root.title("Anime Watch List")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)
        self.root.geometry('+400+250')

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        options_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Reload", command=self.on_reload)
        options_menu.add_command(label="Edit the config file", command=self.on_edit_config)
        options_menu.add_command(label="Open in Github", command=partial(self.on_open_page, 0, 'https://github.com/ahmed91abbas/anime-watch-list'))

        body_frame = tk.Frame(self.root, bg=secondary_color)
        body_frame.pack()

        if not config:
            body_frame.grid_propagate(False)
            tk.Label(body_frame, text="No content found in config.txt", bg=secondary_color, font=('calibri', 22)).grid()
            body_frame.config(width=500, height=300)
            return

        self.canvas = tk.Canvas(body_frame, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(body_frame, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=secondary_color)
        self.canvas.grid_propagate(False)
        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, pady=5)

        if len(config) > max_row_count:
            scrollbar.pack(side="right", fill="y")
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        padx = 15
        pady = 5
        title_width = 45
        component_config = {'height': 2, 'bg': bg_color, 'font': ('calibri', 16), 'highlightthickness': 0, 'border': 0}
        img_width = img_height = component_config['height'] * 29
        elements = []
        for i, c in enumerate(config):
            element = {}
            grid_config = {'pady': pady, 'row': i}
            image = self.get_image_data(c['cover_url'], img_width, img_height)
            img_label = tk.Label(scrollable_frame, image=image)
            img_label.image = image
            img_label.grid(**grid_config, padx=padx, column=0)
            element['img_label'] = img_label
            element['img_width'] = img_width
            element['img_height'] = img_height

            title_button = tk.Button(scrollable_frame, text=self.trim_text(c['title'], title_width), **component_config, width=title_width)
            title_button.grid(**grid_config, column=1)
            element['title_button'] = title_button
            element['title_width'] = title_width

            ep_button = tk.Button(scrollable_frame, text=f'#{c["ep"]}', **component_config, width=5, anchor="w")
            ep_button.grid(**grid_config, column=2)
            element['ep_button'] = ep_button

            button = tk.Button(scrollable_frame, text="Watch next ep", bg=button_color, font=component_config['font'], highlightthickness=2,\
                activebackground=bg_color, state='disabled', compound=tk.CENTER)
            button.grid(**grid_config, padx=padx, column=3)
            element['button'] = button
            elements.append(element)

        self.canvas.update_idletasks()
        row_height = max(img_label.winfo_height(), title_button.winfo_height(), ep_button.winfo_height(), button.winfo_height()) + pady * 2
        row_width = img_label.winfo_width() + title_button.winfo_width() + ep_button.winfo_width() + button.winfo_width() + padx * 4
        self.canvas.config(width=row_width, height=row_height * min(max_row_count, len(config)), yscrollincrement=row_height)
        return elements

    def update_gui(self, config, elements):
        if len(config) != len(elements):
            raise Exception('config and elements must be of the same length')

        for i in range(len(config)):
            c = config[i]
            e = elements[i]

            image = self.get_image_data(c['cover_url'], e['img_width'], e['img_height'])
            e['img_label'].config(image=image)
            e['img_label'].image = image

            e['title_button'].config(text=self.trim_text(c['title'], e['title_width']), command=partial(self.on_open_page, i, c['myanimelist_url']))

            e['ep_button'].config(text=f'#{c["ep"]}', command=partial(self.on_open_page, i, c['current_ep_url'], close=True))

            state  =('disabled', 'normal')[bool(c['next_ep_url'])]
            e['button'].config(state=state, command=partial(self.on_open_page, i, c['next_ep_url'], update_config=True, close=True))

    def get_image_data(self, url, width, height):
        if url:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw_data = urlopen(req).read()
            img = Image.open(io.BytesIO(raw_data))
        else:
            img = Image.open(self.resource_path(os.path.join('images', 'image-not-found.png')))
        img = img.resize((width,height), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)

    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def on_reload(self):
        self.on_close()
        self.run()

    def on_close(self):
        self.root.destroy()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    def on_open_page(self, index, url, update_config=False, close=False):
        if update_config:
            self.config[index]['current_ep_url'] = self.config[index]['next_ep_url']
            self.generator.update_config(self.config)
        webbrowser.open(url, new=0, autoraise=True)
        if close:
            self.on_close()

    def on_edit_config(self):
        file_path = self.generator.get_config_filename()
        if sys.platform.startswith('darwin'):
            subprocess.call('open', file_path)
        elif os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.call('xdg-open', file_path)

    def mainloop(self):
        tk.mainloop()

    def trim_text(self, text, max_length):
        if len(text) > max_length:
            return f'{text[:max_length-3].rstrip()}...'
        return text

if __name__ == '__main__':
    AnimeWatchListGUI()
