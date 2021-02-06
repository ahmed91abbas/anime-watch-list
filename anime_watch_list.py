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
        self.config = self.sort_config(self.generator.get_config())
        self.createGUI(self.config)
        self.mainloop()

    def sort_config(self, config):
        l1 = sorted(list(filter(lambda x: x['next_ep_url'], config)), key=lambda x: x['ep'], reverse=True)
        l2 = sorted(list(filter(lambda x: not x['next_ep_url'], config)), key=lambda x: x['title'])
        return l1 + l2

    def createGUI(self, config, max_row_count=8):
        bg_color = '#e6e6ff'
        secondary_color = '#b28fc7'
        button_color = '#f7e4d0'

        self.root = tk.Tk()
        self.root.configure(background=secondary_color)
        self.root.title("Anime Watch List")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        options_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Edit the config file", command=self.on_edit_config)

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
        title_width = 50
        component_config = {'height': 2, 'bg': bg_color, 'font': ('calibri', 16)}
        for i, c in enumerate(config):
            grid_config = {'pady': pady, 'row': i}
            title_label = tk.Label(scrollable_frame, text=self.trim_text(c['title'], title_width), **component_config, width=title_width)
            title_label.grid(**grid_config, column=0)
            ep_label = tk.Label(scrollable_frame, text=f'#{c["ep"]}', **component_config, width=5, anchor="w")
            ep_label.grid(**grid_config, column=1)
            button = tk.Button(scrollable_frame, text="Watch next ep", bg=button_color, font=component_config['font'], highlightthickness=2,\
                activebackground=bg_color, compound=tk.CENTER, command=partial(self.on_open_page, i, c['next_ep_url']))
            if not c['next_ep_url']:
                button.config(state='disabled')
            button.grid(**grid_config, padx=padx, column=2)

        self.canvas.update_idletasks()
        frame_width = title_label.winfo_width() + ep_label.winfo_width() + button.winfo_width() + padx * 2
        frame_height = (button.winfo_height() + pady * 4) * max_row_count
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
