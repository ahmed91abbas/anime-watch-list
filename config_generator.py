import os
import re
import sys
import json
import base64
import requests
from threading import Thread
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit, quote
from pytz import timezone
from datetime import datetime


class ConfigGenerator:
    def __init__(self, config_filename='config.txt', cache_filename='cache.json'):
        self.base_info = {
            'title': 'Loading...',
            'current_ep_url': '',
            'next_ep_url': '',
            'myanimelist_url': '',
            'ep': '-1',
            'image': {
                'url': '',
                'base64_data': self.get_image_base64_data(None)
            }
        }
        self.url_category_reg = '^https://.*.?gogoanime.[a-z]+/(category/)'
        self.url_reg = '^https://.*.?gogoanime.[a-z]+/.*-episode-(\d+(-\d+)?)$'
        self.config_filename = config_filename
        self.cache_filename = cache_filename
        self.config = []

    def read_json(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return dict()

    def write_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_config_filename(self):
        return self.config_filename

    def add_line_to_config(self, line):
        with open(self.config_filename, 'a') as f:
            f.write(f'{line}\n')

    def update_config(self, config):
        config = sorted(config, key=lambda x: x['title'])
        with open(self.config_filename, 'w') as f:
            for entry in config:
                f.write(f'{entry["current_ep_url"]}\n')

    def get_urls(self):
        with open(self.config_filename, 'r') as f:
            return [line.rstrip() for line in f.readlines()]

    def get_details(self, url):
        try:
            result = self.get_info_from_cache(url)
        except:
            result = self.get_info_from_url(url)
        self.config.append(result)

    def get_info_from_cache(self, url):
        cache = self.cache[url]
        return {
            'title': cache['title'],
            'current_ep_url': cache['current_ep_url'],
            'next_ep_url': cache['next_ep_url'],
            'myanimelist_url': cache['myanimelist_url'],
            'ep': cache['ep'],
            'image': {
                'url': cache['image']['url'],
                'base64_data': cache['image']['base64_data']
            }
        }

    def get_info_from_url(self, url):
        category_match = re.match(self.url_category_reg, url)
        episode_match = re.match(self.url_reg, url)
        result = None
        try:
            if category_match:
                result = self.get_category_page_info(url)
                result['ep'] = '0'
            elif episode_match:
                result = self.get_episode_page_info(url)
                result['ep'] = episode_match.group(1)
        except:
            result = self.get_unsupported_url_info(url, warning_message='Failed')

        if not result:
            result = self.get_unsupported_url_info(url)

        result['current_ep_url'] = url
        result['image']['base64_data'] = self.get_image_base64_data(result['image']['url'])
        return result

    def get_unsupported_url_info(self, url, warning_message='UNSUPPORTED URL'):
        return {**self.base_info, 'title': f'[{warning_message}] {url}'}

    def get_episode_page_info(self, url):
        response = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime-info'}).a.text
        cover_url = soup.find(itemprop='image').get('content')
        myanimelist_url = self.build_myanimelist_url(title)
        next_ep_url = ''
        next_ep_div_a = soup.find('div', {'class': 'anime_video_body_episodes_r'}).a
        if next_ep_div_a:
            next_ep_url = os.path.dirname(url) + next_ep_div_a['href']
        return {'title': title, 'next_ep_url': next_ep_url, 'myanimelist_url': myanimelist_url, 'image': {'url': cover_url}}

    def get_category_page_info(self, url):
        response = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime_info_body_bg'}).h1.text
        cover_url = soup.find(itemprop='image').get('content')
        myanimelist_url = self.build_myanimelist_url(title)
        ep_end = soup.find('div', {'class': 'anime_video_body'}).a.get('ep_end')
        next_ep_url = ''
        if float(ep_end) > 0:
            next_ep_url = self.update_url_episode_number(url, '1')
        else:
            title = f'[Not yet aired] {title}'
        return {'title': title, 'next_ep_url': next_ep_url, 'myanimelist_url': myanimelist_url, 'image': {'url': cover_url}}

    def update_url_episode_number(self, url, ep):
        if not re.match('^\d+$', ep):
            return url
        episode_match = re.match(self.url_reg, url)
        if episode_match:
            if ep == '0':
                url_with_category = url.replace(os.path.dirname(url), os.path.dirname(url) + '/category')
                return f'{url_with_category.replace(f"-episode-{episode_match.group(1)}", "")}'
            return url.replace(episode_match.group(1), ep)
        category_match = re.match(self.url_category_reg, url)
        if category_match:
            if ep == '0':
                return url
            return f'{url.replace(category_match.group(1), "")}-episode-{ep}'
        return url

    def build_myanimelist_url(self, title):
        return f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime#anime'

    def get_image_base64_data(self, url):
        raw_data = ''
        if url:
            try:
                encoded_url = self.encode_url(url)
                req = Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0'})
                raw_data = urlopen(req).read()
            except:
                pass
        else:
            with open(self.resource_path(os.path.join('images', 'image-not-found.png')), 'rb') as f:
                raw_data = f.read()
        return base64.b64encode(raw_data).decode('utf-8')

    def encode_url(self, url):
        protocol, domain, path, query, fragment = urlsplit(url)
        path = quote(path)
        return urlunsplit((protocol, domain, path, query, fragment))

    def get_skeleton_config(self):
        return [self.base_info]*len(self.get_urls())

    def convert_time_timezone(self, time, tz1, tz2):
        time = datetime.strptime(time, '%H:%M').time()
        dt = datetime.combine(datetime.now(), time)
        tz1 = timezone(tz1)
        tz2 = timezone(tz2)
        return tz1.localize(dt).astimezone(tz2).strftime("%H:%M")

    def get_additional_info(self, title):
        url = "https://api.jikan.moe/v4/anime"
        params = {
            'q': title,
            'limit': '5'
        }
        response = requests.request("GET", url, params=params)
        response = response.json()
        if not 'data' in response:
            return {}
        for item in response['data']:
            for title_object in item['titles']:
                if title == title_object['title']:
                    current_zone = 'Europe/Stockholm'
                    if item["broadcast"]["day"]:
                        time = self.convert_time_timezone(item['broadcast']['time'], item['broadcast']['timezone'], current_zone)
                        broadcast = f'{item["broadcast"]["day"]} at {time} ({current_zone})'
                    else:
                        broadcast = '-'
                    return {
                        'url': item['url'],
                        'title_english': item['title_english'],
                        'source': item['source'],
                        'status': item['status'],
                        'episodes': item['episodes'],
                        'aired': item['aired']['string'],
                        'score': item['score'],
                        'season': item['season'],
                        'broadcast': broadcast,
                        'synopsis': item['synopsis'],
                    }
        return {}

    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def save_cache(self):
        result = {e['current_ep_url']: e for e in self.config if e['next_ep_url']}
        self.write_json(self.cache_filename, result)

    def get_cache(self):
        return self.read_json(self.cache_filename)

    def get_config(self):
        self.cache = self.get_cache()
        self.config = []
        threads = []
        for url in self.get_urls():
            t = Thread(target=self.get_details, args=(url, ))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

        self.save_cache()
        return self.config
