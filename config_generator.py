import os
import requests
import threading
from bs4 import BeautifulSoup


class ConfigGenerator:
    def __init__(self):
        self.config = []

    def get_urls(self):
        with open('config.txt', 'r') as f:
            return [line.rstrip() for line in f.readlines()]

    def get_details(self, url):
        parts = url.split('/')[-1].split('-')
        ep = parts[-1]
        title, next_ep_url = self.get_page_title_and_next_ep_url(url)
        self.config.append({
            'title': title,
            'url': url,
            'next_ep_url': next_ep_url,
            'ep': int(ep)
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
        threads = []
        for url in self.get_urls():
            t = threading.Thread(target=self.get_details, args=(url, ))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        return sorted(sorted(self.config, key=lambda i: i['title']), key=lambda i: i['next_ep_url'], reverse=True)
