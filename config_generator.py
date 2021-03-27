import os
import re
import requests
import threading
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
        category_match = re.match('^https://gogoanime.[a-z]+/category/', url)
        episode_match = re.match('^https://gogoanime.[a-z]+/.*-episode-(\d+(-\d+)?)$', url)
        if category_match:
            title, next_ep_url, myanimelist_url = self.get_category_page_info(url)
            ep = '0'
        elif episode_match:
            title, next_ep_url, myanimelist_url = self.get_episode_page_info(url)
            ep =  episode_match.group(1)
        else:
            title = f'[UNSUPPORTED URL] {url}'
            myanimelist_url = ''
            next_ep_url = ''
            ep = '-1'
        self.config.append({
            'title': title,
            'current_ep_url': url,
            'next_ep_url': next_ep_url,
            'ep': ep,
            'myanimelist_url': myanimelist_url
        })

    def get_episode_page_info(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime-info'}).a.text
        myanimelist_url = self.build_myanimelist_url(title)
        next_ep_url = ''
        try:
            next_ep_href = soup.find('div', {'class': 'anime_video_body_episodes_r'}).a['href']
            next_ep_url = os.path.dirname(url) + next_ep_href
        except:
            pass
        return title, next_ep_url, myanimelist_url

    def get_category_page_info(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime_info_body_bg'}).h1.text
        myanimelist_url = self.build_myanimelist_url(title)
        ep_end = soup.find('div', {'class': 'anime_video_body'}).a.get('ep_end')
        next_ep_url = ''
        if float(ep_end) > 0:
            next_ep_url = f'{url.replace("category/", "")}-episode-1'
        else:
            title = f'[Not yet aired] {title}'
        return title, next_ep_url, myanimelist_url

    def build_myanimelist_url(self, title):
        return f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime#anime'

    def get_config(self):
        self.config = []
        threads = []
        for url in self.get_urls():
            t = threading.Thread(target=self.get_details, args=(url, ))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        return self.config
