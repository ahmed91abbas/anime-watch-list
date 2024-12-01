import os
import re

import requests
from bs4 import BeautifulSoup

from parser_utils import ParserUtils

ALLOWED_DOMAINS = ["gogoanime", "gogoanimes", "anitaku"]

class AnitakuParser(ParserUtils):
    def __init__(self):
        super().__init__()
        url_reg = f"https:\\/\\/.*(?:{'|'.join(ALLOWED_DOMAINS)}).*.[a-z]+"
        self.url_category_reg = re.compile(f"^{url_reg}/(category/)")
        self.url_reg = re.compile(f"^{url_reg}/.*-episode-(\\d+(-\\d+)?)$")
        self.cache_key_sub_reg = re.compile("-episode-\\d+(-\\d+)?")

    def extend_details(self, url, details):
        next_ep_url_from_cache = details.get("next_ep_url")
        category_match = re.match(self.url_category_reg, url)
        episode_match = re.match(self.url_reg, url)
        update_method = None
        if category_match:
            update_method = self.update_with_category_page_info
            details["ep"] = "0"
        elif episode_match:
            update_method = self.update_with_episode_page_info
            details["ep"] = episode_match.group(1)
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
        if details["current_ep_url"] and not details.get("current_url"):
            details["current_url"] = details["current_ep_url"]
        if details["next_ep_url"] and not details.get("next_url"):
            details["next_url"] = details["next_ep_url"]
        return {**self.base_info, **details}

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

    def get_cache_key(self, url):
        return re.sub(self.cache_key_sub_reg, "", url)

    def update_url_episode_number(self, url, ep):
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
