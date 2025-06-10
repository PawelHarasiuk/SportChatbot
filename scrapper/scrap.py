import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_article(url):
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

    article = {'title': title.text, 'text': text.text, 'url': url}
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
    today = datetime.today().strftime('%Y-%m-%d')
    existing_articles = set(os.listdir('./data/articles/'))
    index = 1
    for url in urls:
        article = get_article(root_url + url)
        if article['title'] and article['text']:
            title = f'{today}_{index}.json'
            if title not in existing_articles:
                with open(f'./data/articles/{title}', 'w', encoding='utf-8') as f:
                    json.dump(article, f, ensure_ascii=False)
                index += 1
            else:
                logging.error(f'Article {title} already exists')


scrap()
