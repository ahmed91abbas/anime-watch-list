import base64
import os
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class ParserUtils:
    def __init__(self):
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
            "current_url": "",
            "next_ep_url": "",
            "next_url": "",
            "myanimelist_url": "",
            "mal_id": None,
            "ep": "-1",
            "loaded_from_cache": False,
            "weight": 0,
            "episodes": None,
            "image": {"url": "", "base64_data": self.get_image_base64_data(None)},
        }

    def get_image_base64_data(self, url):
        if url:
            try:
                encoded_url = self.encode_url(url)
                req = Request(encoded_url, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=3) as response:
                    return base64.b64encode(response.read()).decode("utf-8")
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

    def build_myanimelist_url(self, title, mal_id=None):
        if mal_id:
            return f"https://myanimelist.net/anime/{mal_id}"
        return f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime#anime'

    def get_unsupported_url_info(self, url, status):
        return {**self.base_info, "title": url, "status": status, "current_ep_url": url}

    def should_fetch_details_online(self, details):
        return (
            not details.get("title")
            or not details.get("current_ep_url")
            or (not details.get("next_ep_url") and details.get("status") != self.STATUSES["finished"])
            or not details.get("myanimelist_url")
            or not details.get("image", {}).get("url")
        )
