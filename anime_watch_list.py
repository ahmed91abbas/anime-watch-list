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

        if not config:
            body_frame.config(width=500, height=300)
            return

        self.canvas = tk.Canvas(body_frame, bg=bg_color)
        scrollbar = tk.Scrollbar(body_frame, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        self.canvas.grid_propagate(False)
        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)

        padx = 15
        pady = 5
        title_width = 50
        for i, c in enumerate(config):
            grid_config = {'padx': 10, 'pady': 5, 'row': i}
            component_config = {'bg': bg_color, 'font': ('calibri', 16)}
            title_label = tk.Label(scrollable_frame, text=self.trim_text(c['title'], title_width), **component_config, width=title_width)
            title_label.grid(**grid_config, column=0)
            ep_label = tk.Label(scrollable_frame, text=f'#{c["ep"]}', **component_config, width=5)
            ep_label.grid(**grid_config, column=1)
            button = tk.Button(scrollable_frame, text="Watch next ep", **component_config, highlightthickness=1, activebackground=bg_color,\
                state='normal' if c['next_ep_url'] else 'disabled', compound=tk.CENTER, command=partial(self.on_open_page, i, c['next_ep_url']))
            button.grid(**grid_config, column=2)

        self.canvas.update_idletasks()
        frame_width = title_label.winfo_width() + ep_label.winfo_width() + button.winfo_width() + grid_config['padx'] * 6
        frame_height = (button.winfo_height() + grid_config['pady'] * 2) * 10
        self.canvas.config(width=frame_width, height=frame_height)

    def on_close(self):
        self.root.destroy()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

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
