import json
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
    index = 1
    today = datetime.today().strftime('%Y-%m-%d')
    for url in urls:
        article = get_article(root_url + url)
        if article['title'] and article['text']:
            with open(f'../articles/{today}_{index}.json', 'w') as f:
                json.dump(article, f)
            index += 1


scrap()
