import os
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
        with open(self.config_filename, 'w') as f:
            for entry in config:
                f.write(f'{entry["current_ep_url"]}\n')

    def get_urls(self):
        with open(self.config_filename, 'r') as f:
            return [line.rstrip() for line in f.readlines()]

    def get_details(self, url):
        parts = url.split('/')[-1].split('-')
        if '/category/' in url:
            next_ep_url = f'{url.replace("category/", "")}-episode-1'
            title, _ = self.get_page_title_and_next_ep_url(next_ep_url)
            ep = 0
        else:
            title, next_ep_url = self.get_page_title_and_next_ep_url(url)
            ep = parts[-1]
        self.config.append({
            'title': title,
            'current_ep_url': url,
            'next_ep_url': next_ep_url,
            'ep': int(ep),
            'myanimelist_url': f'https://myanimelist.net/search/all?q={"%20".join(title.split(" "))}&cat=anime'
        })

    def get_page_title_and_next_ep_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', {'class': 'anime-info'}).a.text
        next_ep_url = ''
        try:
            next_ep_href = soup.find('div', {'class': 'anime_video_body_episodes_r'}).a['href']
            next_ep_url = os.path.dirname(url) + next_ep_href
        except:
            pass
        return title, next_ep_url

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
