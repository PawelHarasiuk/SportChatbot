import logging

import requests
from bs4 import BeautifulSoup


class MeczykiScrapper:
    def __init__(self):
        self.articles = []

    def _get_article(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f'Error entering website {url}. Status code {response.status_code}')
            return {'title': None, 'text': None, 'url': url}

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h1', class_='news-title')
        text = soup.find('div', class_='news-text-body')

        if not title or not text:
            logging.error(f'Error getting title or text')
            return {'title': None, 'text': None, 'url': url}

        article  = {'title': title.text, 'text': text.text, 'url': url}
        logging.info(f'Success scrapping {url} \n{title}')

        return article

    def _get_urls(self, root_url):
        html = requests.get(root_url).text
        soup = BeautifulSoup(html, 'html.parser')
        links_html = soup.find_all('a', href=True)
        links = []
        for link_html in links_html:
            link = link_html['href']
            if link.startswith('/newsy/'):
                links.append(link)
                logging.info(f'Scrapped {link} from the root url')

        return links

    def scrap(self):
        root_url = 'https://www.meczyki.pl'
        self.articles = []
        urls = self._get_urls(root_url)
        for url in urls:
            article = self._get_article(root_url + url)
            if article['title'] and article['text']:
                self.articles.append(article)

    def get_articles(self):
        return self.articles
