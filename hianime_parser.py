import html
import json
import re

import requests
from bs4 import BeautifulSoup

from parser_utils import ParserUtils

BASE_URL = "https://hianime.nz/"
DISPLAY_EP_URL_PATTERN = re.compile("\\?episode=(\\d+(\\.\\d+)?)$")
EP_URL_PATTERN = re.compile("\\?ep=(\\d+)$")


class HiAnimeParser(ParserUtils):
    def __init__(self):
        super().__init__()

    def extend_details(self, url, details):
        next_ep_url_from_cache = details.get("next_ep_url")
        display_ep_match = DISPLAY_EP_URL_PATTERN.search(url)
        details["ep"] = display_ep_match.group(1) if display_ep_match else "0"
        if not details.get("title") or not details.get("mal_id") or not details.get("image", {}).get("url"):
            try:
                details = self.extend_details_from_page(url, details)
                details["loaded_from_cache"] = False
            except:
                details = self.get_unsupported_url_info(url, self.STATUSES["failed"])
        if not details.get("current_ep_url") or (
            not details.get("next_ep_url") and details.get("status") != self.STATUSES["finished"]
        ):
            try:
                details = self.extend_details_with_ep_data(url, details)
                details["loaded_from_cache"] = False
            except:
                details = self.get_unsupported_url_info(url, self.STATUSES["failed"])
        if details.get("next_ep_url") != next_ep_url_from_cache:
            details["weight"] = 1
        if details["episodes"] == details["ep"]:
            details["status"] = self.STATUSES["finished"]
        if details["ep"] == "0" and not details.get("next_ep_url"):
            details["status"] = self.STATUSES["not_aired"]
        return {**self.base_info, **details}

    def extend_details_with_ep_data(self, url, details):
        anime_id, ep_id, ep_number = self.parse_url(url)
        ep_list_url = f"https://hianime.nz/ajax/v2/episode/list/{anime_id}"
        response = requests.get(ep_list_url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        soup = BeautifulSoup(data["html"], "html.parser")
        ep_items = soup.find_all("a", {"class": "ep-item"})
        current_number, current_id, next_number, next_id = None, None, None, None
        for ep_item in ep_items:
            data_number = ep_item["data-number"]
            data_id = ep_item["data-id"]
            if data_id == ep_id or data_number == ep_number:
                current_number = data_number
                current_id = data_id
            elif current_number or (not ep_number and not ep_id):
                next_number = data_number
                next_id = data_id
                break
        details["ep"] = current_number if current_number else "0"
        details["current_ep_url"] = self.update_url_episode_number(url, current_number)
        details["current_url"] = self.update_url_number(url, current_id)
        if next_number:
            details["next_ep_url"] = self.update_url_episode_number(url, next_number)
            details["next_url"] = self.update_url_number(url, next_id)
        return details

    def extend_details_from_page(self, url, details):
        response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        script = soup.find("script", {"id": "syncData"})
        if script:
            data = json.loads(script.string)
        else:
            raise Exception("Script with syncData not found in the page")
        details["title"] = html.unescape(data.get("name", ""))
        details["mal_id"] = data.get("mal_id")
        details["myanimelist_url"] = self.build_myanimelist_url(details["title"], mal_id=data.get("mal_id"))
        if not details.get("image").get("url"):
            try:
                img_url = soup.find("div", {"class": "film-poster"}).find("img")["src"]
                details["image"] = {}
                details["image"]["url"] = img_url
                details["image"]["base64_data"] = self.get_image_base64_data(details["image"]["url"])
            except:
                pass
        return details

    def get_cache_key(self, url):
        key = re.sub(EP_URL_PATTERN, "", url)
        return re.sub(DISPLAY_EP_URL_PATTERN, "", key).replace("/watch/", "/")

    def update_url_episode_number(self, url, ep):
        base_url = self.get_cache_key(url)
        if ep is None or ep == "0":
            return base_url
        return f"{base_url}?episode={ep}"

    def update_url_number(self, url, ep):
        base_url = self.get_cache_key(url)
        if ep is None or ep == "0":
            return base_url
        parts = base_url.split("/")
        base_url = "/".join(parts[:-1]) + f"/watch/{parts[-1]}"
        return f"{base_url}?ep={ep}"

    def parse_url(self, url):
        anime_id = self.get_cache_key(url).split("-")[-1]
        ep_match = EP_URL_PATTERN.search(url)
        ep_number_match = DISPLAY_EP_URL_PATTERN.search(url)
        if ep_match:
            ep_id = ep_match.group(1)
            ep_number = None
        elif ep_number_match:
            ep_number = ep_number_match.group(1)
            ep_id = None
        else:
            ep_number = None
            ep_id = None
        return anime_id, ep_id, ep_number


if __name__ == "__main__":
    parser = HiAnimeParser()
