import base64
import concurrent.futures
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from pytz import timezone

ALLOWED_DOMAINS = ["gogoanime", "anitaku"]
MAX_THREADS = 8
CONFIG_DIR = "configs"


class ConfigGenerator:
    def __init__(self, config_filename="config.txt", cache_filename="cache.json"):
        self.STATUSES = {
            "default": "",
            "not_aired": "Not yet aired",
            "unsupported_url": "UNSUPPORTED URL",
            "failed": "Failed",
            "finished": "✅",
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
            "episodes": None,
            "image": {"url": "", "base64_data": self.get_image_base64_data(None)},
        }
        url_reg = f"https:\/\/.*(?:{'|'.join(ALLOWED_DOMAINS)}).*.[a-z]+"
        self.url_category_reg = re.compile(f"^{url_reg}/(category/)")
        self.url_reg = re.compile(f"^{url_reg}/.*-episode-(\\d+(-\\d+)?)$")
        self.cache_key_sub_reg = re.compile("-episode-\\d+(-\\d+)?")
        self.title_parentheses_reg = re.compile(r" (\(.*\))$")
        self.title_special_chars_reg = re.compile(r"[^\w\s\-_]")
        self.general_episode_reg = re.compile(r"https://.*-(episode|ep)-(\d+)")
        self.config_filepath = os.path.join(CONFIG_DIR, config_filename)
        self.cache_filepath = os.path.join(CONFIG_DIR, cache_filename)
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

    def get_config_filepath(self):
        return self.config_filepath

    def add_line_to_config(self, line):
        with open(self.config_filepath, "a") as f:
            f.write(f"{line}\n")

    def update_config(self, config):
        config = sorted(config, key=lambda x: x["title"])
        with open(self.config_filepath, "w") as f:
            for entry in config:
                f.write(f'{entry["current_ep_url"]}\n')
        self.save_cache()

    def get_urls(self):
        with open(self.config_filepath, "r") as f:
            return [line.rstrip() for line in f.readlines()]

    def get_details(self, url):
        details = self.get_details_from_cache(url)
        details = self.extend_details(url, details)
        self.config.append(details)

    def get_details_from_cache(self, url):
        cache = self.cache.get(self.get_cache_key(url), {})
        image = cache.get("image", {})
        details = {
            "title": cache.get("title"),
            "current_ep_url": cache.get("current_ep_url"),
            "next_ep_url": cache.get("next_ep_url"),
            "myanimelist_url": cache.get("myanimelist_url"),
            "image": {"url": image.get("url"), "base64_data": image.get("base64_data")},
            "episodes": cache.get("episodes"),
            "loaded_from_cache": True,
        }
        if url != details["current_ep_url"]:
            details["current_ep_url"] = url
            details["next_ep_url"] = ""
        return details

    def extend_details(self, url, details):
        next_ep_url_from_cache = details.get("next_ep_url")
        category_match = re.match(self.url_category_reg, url)
        episode_match = re.match(self.url_reg, url)
        general_episode_match = re.match(self.general_episode_reg, url)
        update_method = None
        if category_match:
            update_method = self.update_with_category_page_info
            details["ep"] = "0"
        elif episode_match:
            update_method = self.update_with_episode_page_info
            details["ep"] = episode_match.group(1)
        elif general_episode_match:
            ep_text = general_episode_match.group(1)
            ep_number = general_episode_match.group(2)
            details["ep"] = ep_number
            details["next_ep_url"] = url.replace(f"-{ep_text}-{ep_number}", f"-{ep_text}-{int(ep_number) + 1}")
            details["title"] = url.rstrip("/").split("/")[-1]
            details["image"]["base64_data"] = self.get_default_image_base64_data()
            return {**self.base_info, **details}
        else:
            details = self.get_unsupported_url_info(url, self.STATUSES["unsupported_url"])
            return {**self.base_info, **details}

        if details["episodes"] == details["ep"]:
            details["status"] = self.STATUSES["finished"]
        elif (
            not details["title"]
            or not details["current_ep_url"]
            or not details["next_ep_url"]
            or not details["myanimelist_url"]
            or not details["image"]["url"]
        ):
            try:
                update_method(url, details)
                details["loaded_from_cache"] = False
            except:
                details = self.get_unsupported_url_info(url, self.STATUSES["failed"])

        if not details["image"]["base64_data"]:
            details["image"]["base64_data"] = self.get_image_base64_data(details["image"]["url"])
            details["loaded_from_cache"] = False
        if details.get("next_ep_url") != next_ep_url_from_cache:
            details["weight"] = 1
        return {**self.base_info, **details}

    def get_unsupported_url_info(self, url, status):
        return {**self.base_info, "title": url, "status": status, "current_ep_url": url}

    def update_with_episode_page_info(self, url, details):
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
        details["title"] = title
        details["current_ep_url"] = url
        details["next_ep_url"] = next_ep_url
        details["myanimelist_url"] = details["myanimelist_url"] or myanimelist_url
        details["image"]["url"] = cover_url

    def update_with_category_page_info(self, url, details):
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
        details["title"] = title
        details["status"] = status
        details["current_ep_url"] = url
        details["next_ep_url"] = next_ep_url
        details["myanimelist_url"] = details["myanimelist_url"] or myanimelist_url
        details["image"]["url"] = cover_url

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
        if url:
            try:
                encoded_url = self.encode_url(url)
                req = Request(encoded_url, headers={"User-Agent": "Mozilla/5.0"})
                return base64.b64encode(urlopen(req).read()).decode("utf-8")
            except:
                pass
        return self.get_default_image_base64_data()

    def get_default_image_base64_data(self):
        with open(os.path.join("images", "image-not-found.png"), "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

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
        filtered_title = self.filter_title(title)
        url = "https://api.jikan.moe/v4/anime"
        params = {"q": filtered_title, "limit": "5"}
        response = requests.request("GET", url, params=params)
        response = response.json()
        if not "data" in response:
            return {}
        for item in response["data"]:
            for title_object in item["titles"]:
                if filtered_title == self.filter_title(title_object["title"]):
                    info = self.map_myanimelist_response(item)
                    self.update_cache({"myanimelist_url": info["url"], "episodes": info["episodes"]}, title)
                    return info
        return {}

    def filter_title(self, title):
        title = re.sub(self.title_parentheses_reg, "", title).rstrip()
        return re.sub(self.title_special_chars_reg, "", title).lower()

    def update_cache(self, fields_to_update, title):
        cache = self.get_cache()
        for k, v in cache.items():
            if v["title"] == title:
                for k2, v2 in fields_to_update.items():
                    cache[k][k2] = v2
                break
        self.write_json(self.cache_filepath, cache)

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
        value = str(value) if value else "-"
        return value if value.startswith("http") else value.capitalize()

    def save_cache(self):
        result = {}
        for e in self.config:
            if e["status"] == self.STATUSES["failed"]:
                continue
            key = self.get_cache_key(e["current_ep_url"])
            result[key] = {
                "title": e["title"],
                "current_ep_url": "" if key in result else e["current_ep_url"],
                "next_ep_url": "" if key in result else e["next_ep_url"],
                "myanimelist_url": e["myanimelist_url"],
                "episodes": e["episodes"],
                "image": {"url": e["image"]["url"], "base64_data": e["image"]["base64_data"]},
            }
        self.write_json(self.cache_filepath, result)

    def get_cache(self):
        return self.read_json(self.cache_filepath)

    def remove_cache(self):
        if os.path.exists(self.cache_filepath):
            os.remove(self.cache_filepath)

    def get_cache_key(self, url):
        return re.sub(self.cache_key_sub_reg, "", url)

    def get_config(self):
        start_time = time.time()
        self.cache = self.get_cache()
        self.config = []
        with concurrent.futures.ThreadPoolExecutor(MAX_THREADS) as executor:
            futures = [executor.submit(self.get_details, url) for url in self.get_urls()]
            concurrent.futures.wait(futures)
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
