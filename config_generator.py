import concurrent.futures
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
from pytz import timezone

from animeheaven_parser import AnimeheavenParser
from anitaku_parser import AnitakuParser
from generic_parser import GenericParser
from hianime_parser import HiAnimeParser
from parser_utils import ParserUtils

MAX_THREADS = 8
CONFIG_DIR = "configs"


class ConfigGenerator(ParserUtils):
    def __init__(self, config_filename="config.txt", cache_filename="cache.json"):
        super().__init__()
        self.title_parentheses_reg = re.compile(r" (\(.*\))$")
        self.title_special_chars_reg = re.compile(r"[^\w\s\-_]")
        self.general_episode_reg = re.compile(r"https://.*-(episode|ep)-(\d+)")
        self.config_filepath = os.path.join(CONFIG_DIR, config_filename)
        self.cache_filepath = os.path.join(CONFIG_DIR, cache_filename)
        self.config = []
        self.parsers = {
            "animeheaven": AnimeheavenParser,
            "anitaku": AnitakuParser,
            "hianime": HiAnimeParser,
            "generic": GenericParser,
        }

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
        details = self.parsers[self.get_domain_name(url)]().extend_details(url, details)
        self.config.append(details)

    def get_details_from_cache(self, url):
        loaded_from_cache = True
        cache = self.cache.get(self.get_cache_key(url), {})
        if not cache:
            loaded_from_cache = False
        details = {**self.base_info, **cache, "loaded_from_cache": loaded_from_cache}
        if url != details["current_ep_url"]:
            details["current_ep_url"] = url
            details["next_ep_url"] = ""
        return details

    def update_url_episode_number(self, url, ep):
        if not ep.isdigit():
            return url
        return self.parsers[self.get_domain_name(url)]().update_url_episode_number(url, ep)

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
        backup_item = None
        for item in response["data"]:
            for title_object in item["titles"]:
                filtered_res_title = self.filter_title(title_object["title"])
                if filtered_title == filtered_res_title:
                    info = self.map_myanimelist_response(item)
                    self.cache_myanimelist_mapped_item(title, info)
                    return info
                elif filtered_res_title in filtered_title or filtered_title in filtered_res_title:
                    backup_item = item
        if backup_item:
            info = self.map_myanimelist_response(backup_item)
            self.cache_myanimelist_mapped_item(title, info)
            return info
        return {}

    def cache_myanimelist_mapped_item(self, title, item):
        fields_to_update = {"myanimelist_url": item["url"], "episodes": item["episodes"]}
        if item["image_url"]:
            base64_image_data = self.get_image_base64_data(item["image_url"])
            image = {
                "url": item["image_url"],
                "base64_data": base64_image_data,
            }
            item["base64_image_data"] = base64_image_data
            fields_to_update["image"] = image
        self.update_cache(fields_to_update, title)

    def filter_title(self, title):
        title = re.sub(self.title_parentheses_reg, "", title).rstrip()
        title = re.sub(r"(\d+)(st|nd|rd|th) season", r"season \1", title, flags=re.IGNORECASE)
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
        img_url = response["images"].get("webp", {}).get("large_image_url", "") or response["images"].get(
            "jpg", {}
        ).get("large_image_url", "")
        return {
            "url": self.stringify(response["url"]),
            "title": self.stringify(response["title"]),
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
            "image_url": img_url,
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
            if not key:
                continue
            result[key] = {
                "title": e["title"],
                "status": e["status"],
                "current_ep_url": "" if key in result else e["current_ep_url"],
                "current_url": "" if key in result else e["current_url"],
                "next_ep_url": "" if key in result else e["next_ep_url"],
                "next_url": "" if key in result else e["next_url"],
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
        return self.parsers[self.get_domain_name(url)]().get_cache_key(url)

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

    def get_domain_name(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(".")[0]
        return domain if domain in self.parsers else "generic"


if __name__ == "__main__":
    gen = ConfigGenerator()
