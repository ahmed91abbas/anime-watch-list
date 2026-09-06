import re
import logging

import requests
from bs4 import BeautifulSoup

from parser_utils import ParserUtils

BASE_URL = "https://anineko.to/"
EP_URL_PATTERN = re.compile("/ep-(\\d+(\\.\\d+)?)$")


class AninekoParser(ParserUtils):
    def __init__(self):
        super().__init__()

    def extend_details(self, url, details):
        next_ep_url_from_cache = details.get("next_ep_url")
        ep_match = EP_URL_PATTERN.search(url)
        base_url = self.get_cache_key(url)
        details["ep"] = ep_match.group(1) if ep_match else "0"
        details["current_ep_url"] = url
        details["current_url"] = url
        if details["episodes"] != details["ep"] and not details.get("next_ep_url"):
            try:
                details = self.extend_details_from_page(base_url, details)
                details["loaded_from_cache"] = False
            except Exception as e:
                logging.error(f"Error occurred while fetching details from page for {url}: {e}")
                details = self.get_unsupported_url_info(url, self.STATUSES["failed"])
        if details.get("next_ep_url") != next_ep_url_from_cache:
            details["weight"] = 1
        details["status"] = self.STATUSES["default"]
        if details["episodes"] == details["ep"]:
            details["status"] = self.STATUSES["finished"]
        if details["ep"] == "0" and not details.get("next_ep_url"):
            details["status"] = self.STATUSES["not_aired"]
        return {**self.base_info, **details}

    def extend_details_from_page(self, url, details):
        current_ep_nbr = int(details.get("ep"))
        response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        title_item = soup.find("div", {"class": "nv-info-main"})
        details["title"] = title_item.find("h1").text.strip() if title_item else ""
        details["myanimelist_url"] = self.build_myanimelist_url(details["title"])
        if not details.get("image", {}).get("url"):
            try:
                img_url = soup.find("aside", {"class": "nv-info-poster"}).find("img")["src"]
                details["image"] = {}
                details["image"]["url"] = img_url
                details["image"]["base64_data"] = self.get_image_base64_data(details["image"]["url"])
            except Exception:
                logging.exception("Failed to load image for Anineko page: %s", url)
        ep_grid = soup.find_all("div", {"class": "nv-info-episode-grid"})
        if ep_grid:
            ep_items = ep_grid[0].find_all("article", {"class": "nv-info-episode-item"})
            for ep_item in ep_items:
                href = ep_item.find("a", {"class": "nv-info-episode-main"})["href"]
                ep_match = EP_URL_PATTERN.search(href)
                if ep_match:
                    ep_number = ep_match.group(1)
                    if int(ep_number) > current_ep_nbr:
                        details["next_ep_url"] = self.update_url_episode_number(url, ep_number)
                        details["next_url"] = details["next_ep_url"]
                        break
        return details

    def get_cache_key(self, url):
        return re.sub(EP_URL_PATTERN, "", url)

    def update_url_episode_number(self, url, ep):
        base_url = self.get_cache_key(url)
        if ep is None or ep == "0":
            return base_url
        return f"{base_url}/ep-{ep}"
