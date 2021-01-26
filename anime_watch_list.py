import webbrowser
import tkinter as tk
from config_generator import ConfigGenerator
from functools import partial


class AnimeWatchListGUI:
    def __init__(self):
        self.generator = ConfigGenerator()
        self.config = self.generator.get_config()
        self.createGUI(self.config)
        self.mainloop()

    def createGUI(self, config):
        bg_color = '#e6e6ff'
        font = ('calibri', 13)
        title_font = ('calibri', 16)
        self.top = tk.Toplevel(bg=bg_color)
        self.top.title("Anime Watch List")
        self.top.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)

        bodyFrame = tk.Frame(self.top, bg=bg_color)
        bodyFrame.pack(pady=15)

        width = 50
        padx = 15
        pady = 5

        for i, c in enumerate(config):
            grid_config = {'padx': 10, 'pady': 5, 'row': i}
            component_config = {'bg': bg_color, 'font': title_font}
            tk.Label(bodyFrame, text=c['title'], **component_config, borderwidth=1).grid(**grid_config, column=0)
            tk.Label(bodyFrame, text=f'#{c["ep"]}', **component_config).grid(**grid_config, column=1)
            button = tk.Button(bodyFrame, text="Watch next ep", **component_config, highlightthickness=1, activebackground=bg_color,\
                state='normal' if c['next_ep_url'] else 'disabled', compound=tk.CENTER, command=partial(self.on_open_page, c['next_ep_url']))
            button.grid(**grid_config, column=2)

    def on_close(self):
        self.top.destroy()

    def on_open_page(self, url):
        webbrowser.open(url, new=0, autoraise=True)

    def mainloop(self):
        tk.mainloop()

if __name__ == '__main__':
    AnimeWatchListGUI()
