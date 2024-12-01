import re

from parser_utils import ParserUtils

EP_GENERIC_PATTERN = re.compile(r"https://.*-(episode|ep)-(\d+)")

class GenericParser(ParserUtils):
    def __init__(self):
        super().__init__()

    def extend_details(self, url, details):
        generic_episode_match = re.match(EP_GENERIC_PATTERN, url)
        if generic_episode_match:
            ep_text = generic_episode_match.group(1)
            ep_number = generic_episode_match.group(2)
            details["ep"] = ep_number
            details["current_ep_url"] = url
            details["current_url"] = url
            details["next_ep_url"] = url.replace(f"-{ep_text}-{ep_number}", f"-{ep_text}-{int(ep_number) + 1}")
            details["next_url"] = details["next_ep_url"]
            details["title"] = url.rstrip("/").split("/")[-1]
            details["loaded_from_cache"] = False
            details["image"]["base64_data"] = self.get_default_image_base64_data()
        else:
            details = self.get_unsupported_url_info(url, self.STATUSES["failed"])
        return {**self.base_info, **details}

    def get_cache_key(self, *args):
        return ""

    def update_url_episode_number(self, url, ep):
        generic_episode_match = re.match(EP_GENERIC_PATTERN, url)
        if generic_episode_match:
            ep_text = generic_episode_match.group(1)
            ep_number = generic_episode_match.group(2)
            url.replace(f"-{ep_text}-{ep_number}", f"-{ep_text}-{ep}")
        return url
