import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from functools import partial
from threading import Thread
from tkinter import messagebox

from additional_info_gui import AdditionalInfoGUI
from config_generator import ConfigGenerator
from gui_utils import GuiUtils
from settings_gui import SettingsGUI


class AnimeWatchListGUI(GuiUtils):
    def __init__(self):
        self.defaults = {"max_rows": 8}
        super().__init__(__file__, self.defaults)
        self.components_methods = {key: [] for key in self.theme_color_keys}
        self.generator = ConfigGenerator()
        self.run()

    def run(self):
        self.load_theme()
        self.max_rows = self.get_max_rows()
        self.create_gui()
        self.on_reload()
        self.mainloop()

    def add_config_to_gui(self, elements):
        self.config = self.generator.get_config()
        self.config = self.sort_config(self.config)
        self.update_gui(self.config, elements)

    def sort_config(self, config):
        config = sorted(config, key=lambda x: f"{x['status']} {x['title']}")
        l1 = sorted(
            filter(lambda x: x["next_ep_url"], config), key=lambda x: float(x["ep"].replace("-", ".")), reverse=True
        )
        l1 = sorted(l1, key=lambda x: x["weight"], reverse=True)
        l2 = list(filter(lambda x: not x["next_ep_url"], config))
        return l1 + l2

    def create_gui(self):
        self.root = tk.Tk()
        self.root.configure(background=self.secondary_bg_color)
        self.components_methods["secondary_background_color"].append((self.root.configure, "background"))
        self.root.title("Anime Watch List")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)
        self.root.geometry(self.get_geometry())

        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        options_menu = tk.Menu(menu, tearoff=0, bg=self.bg_color, fg=self.text_color)
        self.components_methods["background_color"].append((options_menu.config, "bg"))
        self.components_methods["text_color"].append((options_menu.config, "fg"))
        menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Add to list", command=self.on_add)
        options_menu.add_command(label="Edit", command=self.on_edit)
        options_menu.add_command(label="Reload", command=self.on_reload)
        options_menu.add_command(label="Remove cache", command=self.on_remove_cache)
        options_menu.add_command(label="Show stats", command=self.on_stats)
        options_menu.add_command(label="Edit the config file", command=self.on_edit_config)
        options_menu.add_command(
            label="Open in Github",
            command=partial(self.on_open_page, 0, "https://github.com/ahmed91abbas/anime-watch-list"),
        )
        options_menu.add_command(label="Settings", command=self.on_settings)

        button_config = {
            "font": ("calibri", 12),
            "width": 10,
            "height": 1,
            "bg": self.button_color,
            "fg": self.text_color,
            "activebackground": self.bg_color,
            "compound": tk.CENTER,
            "highlightthickness": 2,
        }
        button_pack_config = {"side": "left", "padx": 5, "pady": 5}
        self.site_frame = tk.Frame(self.root, bg=self.secondary_bg_color)
        self.components_methods["secondary_background_color"].append((self.site_frame.config, "bg"))
        self.site_entry = tk.Entry(
            self.site_frame, width=60, bg=self.bg_color, fg=self.text_color, font=("calibri", 12)
        )
        self.components_methods["background_color"].append((self.site_entry.config, "bg"))
        self.site_entry.pack(side="left", padx=20, pady=5)
        site_add_button = tk.Button(self.site_frame, text="Add", **button_config, command=self.on_site_add)
        self.components_methods["background_color"].append((site_add_button.config, "activebackground"))
        self.components_methods["button_color"].append((site_add_button.config, "bg"))
        self.components_methods["text_color"].append((site_add_button.config, "fg"))
        site_add_button.pack(**button_pack_config)
        site_cancel_button = tk.Button(self.site_frame, text="Cancel", **button_config, command=self.on_site_cancel)
        self.components_methods["background_color"].append((site_cancel_button.config, "activebackground"))
        self.components_methods["button_color"].append((site_cancel_button.config, "bg"))
        self.components_methods["text_color"].append((site_cancel_button.config, "fg"))
        site_cancel_button.pack(**button_pack_config)

        self.edit_frame = tk.Frame(self.root, bg=self.secondary_bg_color)
        self.components_methods["secondary_background_color"].append((self.edit_frame.config, "bg"))
        button_pack_config = {"side": "left", "padx": 15}
        save_button = tk.Button(self.edit_frame, text="Save", **button_config, command=self.on_edit_save)
        self.components_methods["background_color"].append((save_button.config, "activebackground"))
        self.components_methods["button_color"].append((save_button.config, "bg"))
        self.components_methods["text_color"].append((save_button.config, "fg"))
        save_button.pack(**button_pack_config)
        edit_cancel_button = tk.Button(self.edit_frame, text="Cancel", **button_config, command=self.on_edit_cancel)
        self.components_methods["background_color"].append((edit_cancel_button.config, "activebackground"))
        self.components_methods["button_color"].append((edit_cancel_button.config, "bg"))
        self.components_methods["text_color"].append((edit_cancel_button.config, "fg"))
        edit_cancel_button.pack(**button_pack_config)
        self.body_frame = tk.Frame(self.root, bg=self.secondary_bg_color)

    def create_body_frame(self, config):
        body_frame = tk.Frame(self.root, bg=self.secondary_bg_color)

        if not config:
            body_frame.grid_propagate(False)
            self.on_add()
            label = tk.Label(
                body_frame,
                text=f"No content found in {self.generator.get_config_filepath()}",
                bg=self.secondary_bg_color,
                font=("calibri", 22),
            )
            label.grid(padx=15, pady=15)
            body_frame.config(width=822, height=300)
            return body_frame, []

        self.canvas = tk.Canvas(body_frame, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(body_frame, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=self.secondary_bg_color)
        self.components_methods["secondary_background_color"].append((scrollable_frame.config, "bg"))
        self.canvas.grid_propagate(False)
        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, pady=5)

        if len(config) > self.max_rows - 2:
            scrollbar.pack(side="right", fill="y")
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        padx = 15
        pady = 5
        title_width = 45
        component_config = {
            "height": 2,
            "bg": self.bg_color,
            "fg": self.text_color,
            "font": ("calibri", 16),
            "highlightthickness": 0,
            "border": 0,
        }
        img_width = img_height = component_config["height"] * 29
        elements = []
        for i, c in enumerate(config):
            element = {}
            grid_config = {"pady": pady, "row": i}
            image = self.get_image_data(c["image"]["base64_data"], img_width, img_height)
            img_button = tk.Button(scrollable_frame, image=image, border=0, command=partial(self.on_image_button, i))
            img_button.image = image
            img_button.grid(**grid_config, padx=padx, column=0)
            element["img_button"] = img_button
            element["img_width"] = img_width
            element["img_height"] = img_height

            title_button = tk.Button(
                scrollable_frame,
                text=self.trim_text(c["title"], title_width),
                **component_config,
                width=title_width,
            )
            title_button.grid(**grid_config, column=1)
            element["title_button"] = title_button
            element["title_width"] = title_width

            ep_button = tk.Button(scrollable_frame, text=f'#{c["ep"]}', **component_config, width=5, anchor="w")
            ep_button.grid(**grid_config, column=2)
            element["ep_button"] = ep_button

            ep_entry = tk.Entry(scrollable_frame, width=3, font=component_config["font"], fg=self.text_color)
            element["ep_entry"] = ep_entry

            main_button_config = {
                "bg": self.button_color,
                "fg": self.text_color,
                "activebackground": self.bg_color,
                "compound": tk.CENTER,
                "highlightthickness": 2,
                "font": component_config["font"],
                "width": 12,
            }
            watch_button = tk.Button(scrollable_frame, text="Watch next ep", state="disabled", **main_button_config)
            watch_button.grid(**grid_config, padx=padx, column=3)
            element["watch_button"] = watch_button

            remove_button = tk.Button(
                scrollable_frame, text="Remove", **main_button_config, command=partial(self.on_remove_button, i)
            )
            element["remove_button"] = remove_button

            element["marked_for_deletion"] = False
            element["bg_color"] = self.bg_color

            elements.append(element)

        self.canvas.update_idletasks()
        row_height = (
            max(
                img_button.winfo_height(),
                title_button.winfo_height(),
                ep_button.winfo_height(),
                watch_button.winfo_height(),
            )
            + pady * 2
        )
        row_width = (
            img_button.winfo_width()
            + title_button.winfo_width()
            + ep_button.winfo_width()
            + watch_button.winfo_width()
            + padx * 4
        )
        self.row_height = row_height
        self.site_frame["height"] = row_height
        self.edit_frame["height"] = row_height
        self.row_count = min(self.max_rows, len(config), self.row_count)
        self.canvas.config(width=row_width, height=row_height * self.row_count, yscrollincrement=row_height)
        return body_frame, elements

    def update_gui(self, config, elements):
        self.add_icon(self.root)
        if len(config) != len(elements):
            raise Exception("config and elements must be of the same length")

        for i in range(len(config)):
            c = config[i]
            e = elements[i]

            image = self.get_image_data(c["image"]["base64_data"], e["img_width"], e["img_height"])
            e["img_button"].config(image=image)
            e["img_button"].image = image
            title = f"[{c['status']}] {c['title']}" if c["status"] else c["title"]
            e["title_button"].config(
                text=self.trim_text(title, e["title_width"]),
                command=partial(self.on_open_page, i, c["myanimelist_url"]),
            )
            e["ep_button"].config(
                text=f'#{c["ep"]}', command=partial(self.on_open_page, i, c["current_url"], close=True)
            )
            state = ("disabled", "normal")[bool(c["next_ep_url"])]
            e["watch_button"].config(
                state=state, command=partial(self.on_open_page, i, c["next_url"], update_config=True, close=True)
            )

    def update_canvas_rows(self, diff):
        if len(self.config) >= self.max_rows and self.row_count + diff <= self.max_rows:
            self.row_count += diff
            self.canvas["height"] = self.row_height * self.row_count

    def is_valid_url(self, text):
        return (
            isinstance(text, str) and len(text) >= 12 and (text.startswith("http://") or text.startswith("https://"))
        )

    def on_add(self):
        self.site_entry.delete(0, "end")
        self.site_frame.grid(row=0, padx=10, pady=15)
        self.update_canvas_rows(-1)
        try:
            clipboard = self.root.clipboard_get()
        except:
            clipboard = ""
        if self.is_valid_url(clipboard):
            self.site_entry.insert(0, clipboard)

    def on_site_add(self):
        site = self.site_entry.get().rstrip()
        if self.is_valid_url(site):
            self.generator.add_line_to_config(site)
            self.on_reload()
        self.on_site_cancel()

    def on_site_cancel(self):
        self.update_canvas_rows(1)
        self.site_frame.grid_forget()

    def on_edit_save(self):
        for i, e in reversed(list(enumerate(self.elements))):
            ep = e["ep_entry"].get()
            if e["marked_for_deletion"]:
                del self.config[i]
            elif ep != self.config[i]["ep"]:
                new_url = self.generator.update_url_episode_number(self.config[i]["current_ep_url"], ep)
                self.config[i]["current_ep_url"] = new_url
                self.config[i]["next_ep_url"] = ""
        self.generator.update_config(self.config)
        self.on_reload()
        self.on_edit_cancel()

    def on_edit_cancel(self):
        self.update_canvas_rows(1)
        self.edit_frame.grid_forget()
        for e in self.elements:
            e["ep_entry"].grid_forget()
            e["ep_button"]["state"] = "normal"
            e["remove_button"].grid_forget()
            e["title_button"]["bg"] = e["bg_color"]
            e["ep_button"]["bg"] = e["bg_color"]
            e["marked_for_deletion"] = False

    def on_reload(self):
        self.load_theme()
        self.max_rows = self.get_max_rows()
        self.row_count = sys.maxsize
        body_frame, elements = self.create_body_frame(self.generator.get_skeleton_config())
        body_frame.grid(row=1)
        self.body_frame.destroy()
        self.body_frame = body_frame
        self.elements = elements
        Thread(target=self.add_config_to_gui, args=(self.elements,)).start()

    def load_theme(self):
        self.bg_color = self.get_color("background_color")
        self.secondary_bg_color = self.get_color("secondary_background_color")
        self.button_color = self.get_color("button_color")
        self.text_color = self.get_color("text_color")

    def on_stats(self):
        stats = self.generator.get_stats()
        stats = "\n".join([f'{k.capitalize().replace("_", " ")}: {v}' for k, v in stats.items()])
        messagebox.showinfo("Stats", stats)

    def on_remove_cache(self):
        self.generator.remove_cache()

    def on_close(self):
        self.set_geometry(self.root.geometry())
        self.root.destroy()

    def on_mousewheel(self, event):
        if str(self.root.focus_get()) == ".":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def on_open_page(self, index, url, update_config=False, close=False):
        if not self.is_valid_url(url):
            return
        if update_config:
            self.config[index]["current_ep_url"] = self.config[index]["next_ep_url"]
            self.config[index]["next_ep_url"] = ""
            self.generator.update_config(self.config)
        webbrowser.open(url, new=0, autoraise=True)
        if close:
            self.on_close()

    def on_edit_config(self):
        file_path = self.generator.get_config_filepath()
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", file_path])
        else:
            subprocess.call(["xdg-open", file_path])

    def on_edit(self):
        if not self.elements:
            return
        self.edit_frame.grid(row=2, pady=20)
        self.update_canvas_rows(-1)
        for i, e in enumerate(self.elements):
            e["ep_entry"].delete(0, "end")
            e["ep_entry"].insert(0, self.config[i]["ep"])
            e["ep_entry"].grid(row=i, column=2)
            e["ep_button"]["state"] = "disabled"
            e["remove_button"].grid(row=i, column=3)

    def on_remove_button(self, index):
        color = self.elements[index]["bg_color"] if self.elements[index]["marked_for_deletion"] else "orange red"
        self.elements[index]["title_button"]["bg"] = color
        self.elements[index]["ep_button"]["bg"] = color
        self.elements[index]["marked_for_deletion"] = not self.elements[index]["marked_for_deletion"]

    def on_image_button(self, index):
        AdditionalInfoGUI(self.config[index]["title"], self.config[index]["image"]["base64_data"])

    def on_settings(self):
        for element in self.elements:
            self.components_methods["background_color"].append((element["title_button"].config, "bg"))
            self.components_methods["background_color"].append((element["ep_button"].config, "bg"))
            self.components_methods["background_color"].append((element["watch_button"].config, "activebackground"))
            self.components_methods["background_color"].append((element["remove_button"].config, "activebackground"))
            self.components_methods["button_color"].append((element["watch_button"].config, "bg"))
            self.components_methods["button_color"].append((element["remove_button"].config, "bg"))
            self.components_methods["secondary_background_color"].append((self.body_frame.config, "bg"))
            self.components_methods["text_color"].append((element["title_button"].config, "fg"))
            self.components_methods["text_color"].append((element["ep_button"].config, "fg"))
            self.components_methods["text_color"].append((element["watch_button"].config, "fg"))
            self.components_methods["text_color"].append((element["remove_button"].config, "fg"))
            self.components_methods["text_color"].append((element["ep_entry"].config, "fg"))

        self.settings_gui = SettingsGUI(self.components_methods)

    def mainloop(self):
        tk.mainloop()


if __name__ == "__main__":
    AnimeWatchListGUI()
