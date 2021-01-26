import sys
import os
import subprocess
import webbrowser
import tkinter as tk
from functools import partial
from config_generator import ConfigGenerator


class AnimeWatchListGUI:
    def __init__(self):
        self.generator = ConfigGenerator()
        self.config = self.generator.get_config()
        self.createGUI(self.config)
        self.mainloop()

    def createGUI(self, config):
        bg_color = '#e6e6ff'

        self.root = tk.Tk()
        self.root.configure(background=bg_color)
        self.root.title("Anime Watch List")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        options_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Edit the config file", command=self.on_edit_config)

        body_frame = tk.Frame(self.root, bg=bg_color)
        body_frame.pack(pady=15)

        width = 50
        padx = 15
        pady = 5
        title_width = 50

        for i, c in enumerate(config):
            grid_config = {'padx': 10, 'pady': 5, 'row': i}
            component_config = {'bg': bg_color, 'font': ('calibri', 16)}
            tk.Label(body_frame, text=self.trim_text(c['title'], title_width), **component_config, width=title_width).grid(**grid_config, column=0)
            tk.Label(body_frame, text=f'#{c["ep"]}', **component_config, width=5).grid(**grid_config, column=1)
            button = tk.Button(body_frame, text="Watch next ep", **component_config, highlightthickness=1, activebackground=bg_color,\
                state='normal' if c['next_ep_url'] else 'disabled', compound=tk.CENTER, command=partial(self.on_open_page, i, c['next_ep_url']))
            button.grid(**grid_config, column=2)

    def on_close(self):
        self.root.destroy()

    def on_open_page(self, index, url):
        self.config[index]['url'] = self.config[index]['next_ep_url']
        self.generator.update_config(self.config)
        webbrowser.open(url, new=0, autoraise=True)
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
