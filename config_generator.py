import os
import re
import requests
from threading import Thread
from bs4 import BeautifulSoup


class ConfigGenerator:
    def __init__(self, config_filename='config.txt'):
        self.config_filename = config_filename
        self.config = []

    def get_config_filename(self):
        return self.config_filename

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
        category_match = re.match('^https://.*.?gogoanime.[a-z]+/category/', url)
        episode_match = re.match('^https://.*.?gogoanime.[a-z]+/.*-episode-(\d+(-\d+)?)$', url)
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
            result['ep'] = '-1'

        if not result:
            result = self.get_unsupported_url_info(url)
            result['ep'] = '-1'

        result['current_ep_url'] = url
        return result

    def get_unsupported_url_info(self, url, warning_message='UNSUPPORTED URL'):
        return {'title': f'[{warning_message}] {url}', 'next_ep_url': '', 'myanimelist_url': '', 'cover_url': ''}

    def get_episode_page_info(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime-info'}).a.text
        cover_url = soup.find(itemprop='image').get('content')
        myanimelist_url = self.build_myanimelist_url(title)
        next_ep_url = ''
        next_ep_div_a = soup.find('div', {'class': 'anime_video_body_episodes_r'}).a
        if next_ep_div_a:
            next_ep_url = os.path.dirname(url) + next_ep_div_a['href']
        return {'title': title, 'next_ep_url': next_ep_url, 'myanimelist_url': myanimelist_url, 'cover_url': cover_url}

    def get_category_page_info(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime_info_body_bg'}).h1.text
        cover_url = soup.find(itemprop='image').get('content')
        myanimelist_url = self.build_myanimelist_url(title)
        ep_end = soup.find('div', {'class': 'anime_video_body'}).a.get('ep_end')
        next_ep_url = ''
        if float(ep_end) > 0:
            next_ep_url = f'{url.replace("category/", "")}-episode-1'
        else:
            title = f'[Not yet aired] {title}'
        return {'title': title, 'next_ep_url': next_ep_url, 'myanimelist_url': myanimelist_url, 'cover_url': cover_url}

    def build_myanimelist_url(self, title):
        return f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime#anime'

    def get_skeleton_config(self):
        data = {'title': 'Loading...', 'current_ep_url': '', 'next_ep_url': '', 'myanimelist_url': '', 'cover_url': '', 'ep': '-1'}
        return [data]*len(self.get_urls())

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
