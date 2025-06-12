import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from pymongo import MongoClient
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:password@localhost:27017/')
client = MongoClient(mongodb_uri, unicode_decode_error_handler='ignore')
db = client['scraper_db']
articles_collection = db['articles']



def get_article(url):
    response = requests.get(url)
    response.encoding = response.apparent_encoding

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

    article = {
        'title': title.text.strip(),
        'text': text.text.strip(),
        'url': url,
        'scraped_at': datetime.utcnow()
    }

    logging.info(f'Success scrapping {url} \n{title}')

    return article

def get_urls(root_url):
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

def scrap():
    root_url = 'https://www.meczyki.pl'
    urls = get_urls(root_url)

    for url in urls:
        full_url = root_url + url
        if not articles_collection.find_one({'url': full_url}):
            article = get_article(full_url)
            if article['title'] and article['text']:
                try:
                    articles_collection.insert_one(article)
                    logging.info(f'Stored article "{article["title"]}" in MongoDB')
                except Exception as e:
                    logging.error(f'Error storing article in MongoDB: {e}')
        else:
            logging.info(f'Article with URL {full_url} already exists in database')

if __name__ == "__main__":
    scrap()