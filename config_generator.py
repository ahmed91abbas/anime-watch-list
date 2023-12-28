import base64
import json
import os
import re
import sys
import time
from datetime import datetime
from threading import Thread
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from pytz import timezone

ALLOWED_DOMAINS = ["gogoanime", "anitaku"]

class ConfigGenerator:
    def __init__(self, config_filename="config.txt", cache_filename="cache.json"):
        self.STATUSES = {
            "default": "",
            "not_aired": "Not yet aired",
            "unsupported_url": "UNSUPPORTED URL",
            "failed": "Failed",
        }
        self.base_info = {
            "title": "Loading...",
            "status": "",
            "current_ep_url": "",
            "next_ep_url": "",
            "myanimelist_url": "",
            "ep": "-1",
            "loaded_from_cache": False,
            "weight": 0,
            "image": {"url": "", "base64_data": self.get_image_base64_data(None)},
        }
        url_reg = f"https:\/\/.*(?!{'|'.join(ALLOWED_DOMAINS)}).*.[a-z]+"
        self.url_category_reg = re.compile(f"^{url_reg}/(category/)")
        self.url_reg = re.compile(f"^{url_reg}/.*-episode-(\\d+(-\\d+)?)$")
        self.config_filename = config_filename
        self.cache_filename = cache_filename
        self.config = []

    def read_json(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return dict()

    def write_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def get_config_filename(self):
        return self.config_filename

    def add_line_to_config(self, line):
        with open(self.config_filename, "a") as f:
            f.write(f"{line}\n")

    def update_config(self, config):
        config = sorted(config, key=lambda x: x["title"])
        with open(self.config_filename, "w") as f:
            for entry in config:
                f.write(f'{entry["current_ep_url"]}\n')

    def get_urls(self):
        with open(self.config_filename, "r") as f:
            return [line.rstrip() for line in f.readlines()]

    def get_details(self, url):
        try:
            result = self.get_info_from_cache(url)
        except:
            result = self.get_info_from_url(url)
        self.config.append(result)

    def get_info_from_cache(self, url):
        cache = self.cache[url]
        info = {
            "title": cache["title"],
            "status": cache["status"],
            "current_ep_url": cache["current_ep_url"],
            "next_ep_url": cache["next_ep_url"],
            "myanimelist_url": cache["myanimelist_url"],
            "ep": cache["ep"],
            "loaded_from_cache": True,
            "image": {"url": cache["image"]["url"], "base64_data": cache["image"]["base64_data"]},
        }
        return {**self.base_info, **info}

    def get_info_from_url(self, url):
        category_match = re.match(self.url_category_reg, url)
        episode_match = re.match(self.url_reg, url)
        result = None
        try:
            if category_match:
                result = self.get_category_page_info(url)
                result["ep"] = "0"
            elif episode_match:
                result = self.get_episode_page_info(url)
                result["ep"] = episode_match.group(1)
        except:
            result = self.get_unsupported_url_info(url, self.STATUSES["failed"])

        if not result:
            result = self.get_unsupported_url_info(url, self.STATUSES["unsupported_url"])
        if not result.get("current_ep_url"):
            result["current_ep_url"] = url
        result["image"]["base64_data"] = self.get_image_base64_data(result["image"]["url"])
        if result["next_ep_url"]:
            result["weight"] = 1
        return {**self.base_info, **result}

    def get_unsupported_url_info(self, url, status):
        return {**self.base_info, "title": url, "status": status}

    def get_episode_page_info(self, url):
        response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        url = response.url
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("div", {"class": "anime-info"}).a.text
        cover_url = soup.find(itemprop="image").get("content")
        myanimelist_url = self.build_myanimelist_url(title)
        next_ep_url = ""
        next_ep_div_a = soup.find("div", {"class": "anime_video_body_episodes_r"}).a
        if next_ep_div_a:
            next_ep_url = os.path.dirname(url) + next_ep_div_a["href"]
        return {
            "title": title,
            "current_ep_url": url,
            "next_ep_url": next_ep_url,
            "myanimelist_url": myanimelist_url,
            "image": {"url": cover_url},
        }

    def get_category_page_info(self, url):
        response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("div", {"class": "anime_info_body_bg"}).h1.text
        cover_url = soup.find(itemprop="image").get("content")
        myanimelist_url = self.build_myanimelist_url(title)
        ep_end = soup.find("div", {"class": "anime_video_body"}).a.get("ep_end")
        next_ep_url = ""
        status = self.STATUSES["default"]
        if float(ep_end) > 0:
            next_ep_url = self.update_url_episode_number(url, "1")
        else:
            status = self.STATUSES["not_aired"]
        return {
            "title": title,
            "status": status,
            "next_ep_url": next_ep_url,
            "myanimelist_url": myanimelist_url,
            "image": {"url": cover_url},
        }

    def update_url_episode_number(self, url, ep):
        if not ep.isdigit():
            return url
        episode_match = re.match(self.url_reg, url)
        if episode_match:
            if ep == "0":
                url_with_category = url.replace(os.path.dirname(url), os.path.dirname(url) + "/category")
                return f'{url_with_category.replace(f"-episode-{episode_match.group(1)}", "")}'
            return url.replace(episode_match.group(1), ep)
        category_match = re.match(self.url_category_reg, url)
        if category_match:
            if ep == "0":
                return url
            return f'{url.replace(category_match.group(1), "")}-episode-{ep}'
        return url

    def build_myanimelist_url(self, title):
        return f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime#anime'

    def get_image_base64_data(self, url):
        raw_data = ""
        if url:
            try:
                encoded_url = self.encode_url(url)
                req = Request(encoded_url, headers={"User-Agent": "Mozilla/5.0"})
                raw_data = urlopen(req).read()
            except:
                pass
        else:
            with open(self.resource_path(os.path.join("images", "image-not-found.png")), "rb") as f:
                raw_data = f.read()
        return base64.b64encode(raw_data).decode("utf-8")

    def encode_url(self, url):
        protocol, domain, path, query, fragment = urlsplit(url)
        path = quote(path)
        return urlunsplit((protocol, domain, path, query, fragment))

    def get_skeleton_config(self):
        return [self.base_info] * len(self.get_urls())

    def convert_time_timezone(self, day, time, tz1, tz2):
        days = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"]
        time = datetime.strptime(time, "%H:%M").time()
        dt = datetime.combine(datetime.now(), time)
        tz1 = timezone(tz1)
        tz2 = timezone(tz2)
        converted_date = tz1.localize(dt).astimezone(tz2)
        day_diff = int(dt.strftime("%d")) - int(converted_date.strftime("%d"))
        converted_time = converted_date.strftime("%H:%M")
        if day_diff == 0:
            return day, converted_time
        if day_diff > 0 or day_diff <= -29:
            return days[days.index(day) - 1], converted_time
        return days[(days.index(day) + 1) % len(days)], converted_time

    def get_additional_info(self, title):
        m = re.match(r".* (\(.*\))", title)
        if m:
            title = title.replace(m.group(1), "").rstrip()
        url = "https://api.jikan.moe/v4/anime"
        params = {"q": title, "limit": "5"}
        response = requests.request("GET", url, params=params)
        response = response.json()
        if not "data" in response:
            return {}
        for item in response["data"]:
            for title_object in item["titles"]:
                if title == title_object["title"]:
                    return self.map_myanimelist_response(item)
        return {}

    def map_myanimelist_response(self, response):
        current_zone = "Europe/Stockholm"
        if response["broadcast"]["day"]:
            day, time = self.convert_time_timezone(
                response["broadcast"]["day"],
                response["broadcast"]["time"],
                response["broadcast"]["timezone"],
                current_zone,
            )
            broadcast = f"{day} at {time} ({current_zone})"
        else:
            broadcast = "-"
        genres = [self.stringify(genre["name"]) for genre in response["genres"]]
        return {
            "url": self.stringify(response["url"]),
            "title_english": self.stringify(response["title_english"]),
            "source": self.stringify(response["source"]),
            "status": self.stringify(response["status"]),
            "episodes": self.stringify(response["episodes"]),
            "aired": self.stringify(response["aired"]["string"]),
            "score": self.stringify(response["score"]),
            "season": self.stringify(response["season"]),
            "broadcast": self.stringify(broadcast),
            "genres": ", ".join(genres),
            "synopsis": self.stringify(response["synopsis"]),
        }

    def stringify(self, value):
        return str(value).capitalize() if value else "-"

    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def save_cache(self):
        result = {e["current_ep_url"]: e for e in self.config if e["next_ep_url"]}
        self.write_json(self.cache_filename, result)

    def get_cache(self):
        return self.read_json(self.cache_filename)

    def remove_cache(self):
        if os.path.exists(self.cache_filename):
            os.remove(self.cache_filename)

    def get_config(self):
        start_time = time.time()
        self.cache = self.get_cache()
        self.config = []
        threads = []
        for url in self.get_urls():
            t = Thread(target=self.get_details, args=(url,))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

        self.save_cache()
        self.update_config(self.config)
        self.config_load_time = time.time() - start_time
        return self.config

    def get_stats(self):
        stats = {
            "total": 0,
            "cached": 0,
            "not_aired": 0,
            "not_started": 0,
            "failed": 0,
            "without_next_episode": 0,
            "config_load_time": "N/A",
        }
        if not self.config:
            return stats
        stats["total"] = len(self.config)
        stats["config_load_time"] = f"{self.config_load_time: .3f}s" if self.config_load_time else "N/A"
        for c in self.config:
            if c["loaded_from_cache"]:
                stats["cached"] += 1
            if c["status"] == self.STATUSES["not_aired"]:
                stats["not_aired"] += 1
            if c["ep"] == "0":
                stats["not_started"] += 1
            if c["status"] == self.STATUSES["failed"] or c["status"] == self.STATUSES["unsupported_url"]:
                stats["failed"] += 1
            if c["status"] == self.STATUSES["default"] and not c["next_ep_url"]:
                stats["without_next_episode"] += 1
        return stats


if __name__ == "__main__":
    gen = ConfigGenerator()
