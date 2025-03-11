import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from parser_utils import ParserUtils

BASE_URL = "https://animeheaven.me/"
EP_URL_PATTERN = re.compile("&episode=(\\d+(\\.\\d+)?)$")
EP_TITLE_PATTERN = re.compile(" Episode (\\d+(\\.\\d+)?)$")


class AnimeheavenParser(ParserUtils):
    def __init__(self):
        super().__init__()

    def extend_details(self, url, details):
        next_ep_url_from_cache = details.get("next_ep_url")
        details["ep"] = self.get_ep_from_url(url)
        if details["episodes"] == details["ep"]:
            details["status"] = self.STATUSES["finished"]
        if self.should_fetch_details_online(details):
            try:
                ep, main_url = self.get_main_url(url)
                details = self.extend_details_from_main_page(ep, main_url, details)
                details["loaded_from_cache"] = False
            except:
                details = self.get_unsupported_url_info(url, self.STATUSES["failed"])
        if details.get("next_ep_url") != next_ep_url_from_cache:
            details["weight"] = 1
        return {**self.base_info, **details}

    def get_ep_from_url(self, url):
        ep_match = re.search(EP_URL_PATTERN, url)
        return ep_match.group(1) if ep_match else "0"

    def get_main_url(self, url):
        ep = self.get_ep_from_url(url)
        if "anime.php" in url:
            return ep, re.sub(EP_URL_PATTERN, "", url)
        elif "episode.php" not in url:
            raise Exception(f"Invalid animeheaven url: {url}")
        try:
            response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")
            h1 = soup.find("h1")
            relative_url = h1.find("a").attrs["href"]
            ep_match = re.search(EP_TITLE_PATTERN, h1.text)
            if ep_match:
                ep = ep_match.group(1)
            return ep, urljoin(BASE_URL, relative_url)
        except Exception as e:
            raise Exception(f"Could not parse animeheaven url: {url}. Error: {e}")

    def extend_details_from_main_page(self, ep, url, details):
        details["ep"] = ep
        details["current_ep_url"] = f"{url}&episode={ep}"
        details["current_url"] = details["current_ep_url"]
        response = requests.get(url, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        ep_classes = soup.find_all("a", {"class": "ac3"})
        found = False
        for ep_class in ep_classes:
            ep_class_url = urljoin(BASE_URL, ep_class["href"])
            ep_class_text = ep_class.find("div", class_=lambda c: c and c.startswith("watch2 bc")).text
            if "raw" in ep_class_text:
                continue
            if ep_class_text == ep:
                details["current_url"] = ep_class_url
                found = True
                break
            details["next_url"] = ep_class_url
            details["next_ep_url"] = f"{url}&episode={ep_class_text}"

        if not found and ep != "0":
            details["status"] = self.STATUSES["not_aired"]
            details["current_url"] = ""
            details["next_url"] = ""
            details["next_ep_url"] = ""

        details["title"] = soup.find("div", {"class": "infotitle c"}).text

        if not details.get("myanimelist_url"):
            details["myanimelist_url"] = details.get("myanimelist_url") or self.build_myanimelist_url(details["title"])

        if not details.get("image"):
            details["image"] = {}
            details["image"]["url"] = soup.find("img", {"class": "posterimg"})["src"]
            details["image"]["base64_data"] = self.get_image_base64_data(details["image"]["url"])

        if details.get("episodes", "") == details["ep"]:
            details["status"] = self.STATUSES["finished"]
        return details

    def get_cache_key(self, url):
        return re.sub(EP_URL_PATTERN, "", url) if "anime.php" in url else ""

    def update_url_episode_number(self, url, ep):
        main_url = re.sub(EP_URL_PATTERN, "", url)
        return f"{main_url}&episode={ep}" if "anime.php" in url else url


if __name__ == "__main__":
    parser = AnimeheavenParser()
