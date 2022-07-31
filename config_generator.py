import os
import re
import sys
import requests
from threading import Thread
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit, quote
from pytz import timezone
from datetime import datetime


class ConfigGenerator:
    def __init__(self, config_filename='config.txt'):
        self.base_info = {
            'title': 'Loading...',
            'current_ep_url': '',
            'next_ep_url': '',
            'myanimelist_url': '',
            'ep': '-1',
            'image': {
                'url': '',
                'raw_data': self.get_image_data(None)
            }
        }
        self.url_category_reg = '^https://.*.?gogoanime.[a-z]+/(category/)'
        self.url_reg = '^https://.*.?gogoanime.[a-z]+/.*-episode-(\d+(-\d+)?)$'
        self.config_filename = config_filename
        self.config = []

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
        result = self.get_info_from_url(url)
        for key in result:
            if key.endswith('_url'):
                result[key] = result[key].replace(' ', '%20')
        self.config.append(result)

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
        result['image']['raw_data'] = self.get_image_data(result['image']['url'])
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

    def get_image_data(self, url):
        if url:
            try:
                encoded_url = self.encode_url(url)
                req = Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0'})
                raw_data = urlopen(req).read()
                return raw_data
            except:
                pass
        with open(self.resource_path(os.path.join('images', 'image-not-found.png')), 'rb') as f:
            raw_data = f.read()
        return raw_data

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
            return self.get_skeleton_additional_info()
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
                        'source': item['source'],
                        'status': item['status'],
                        'episodes': item['episodes'],
                        'aired': item['aired']['string'],
                        'score': item['score'],
                        'season': item['season'],
                        'broadcast': broadcast,
                    }
        return self.get_skeleton_additional_info()

    def get_skeleton_additional_info(self):
        return {
                'url': '-',
                'source': '-',
                'status': '-',
                'episodes': '-',
                'aired': '-',
                'score': '-',
                'season': '-',
                'broadcast': '-',
            }

    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def get_config(self):
        self.config = []
        threads = []
        for url in self.get_urls():
            t = Thread(target=self.get_details, args=(url, ))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        return self.config
