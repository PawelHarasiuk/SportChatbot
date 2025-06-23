from urllib.parse import urljoin
import os
import time
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bs4 import BeautifulSoup
from selenium.webdriver import Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import tempfile

def create_driver():
    remote_url = os.getenv('SELENIUM_REMOTE_URL')
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Create a unique temporary directory for Chrome user data
    tmp_profile = tempfile.mkdtemp(prefix="chrome-user-data-")
    options.add_argument(f"--user-data-dir={tmp_profile}")
    # (Optionally) disable GPU, extensions, etc.
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-extensions")
    caps = DesiredCapabilities.CHROME.copy()
    caps.update(options.to_capabilities())
    if remote_url:
        try:
            driver = Remote(command_executor=remote_url, options=options)
            logging.debug(f"Connected to Selenium at {remote_url}, using profile {tmp_profile}")
        except Exception as e:
            logging.error(f"Error initializing Selenium Remote WebDriver: {e}")
            # Optionally: clean up the temp dir on error?
            raise
    else:
        from selenium import webdriver
        driver = webdriver.Chrome(options=options)
    return driver

# Later in code:
driver = create_driver()

def get_mongo_client_with_retry(uri, max_retries=10, delay_seconds=3):
    for attempt in range(1, max_retries + 1):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            logging.info("Connected to MongoDB")
            return client
        except ServerSelectionTimeoutError as e:
            logging.warning(f"MongoDB connection attempt {attempt}/{max_retries} failed: {e}")
            time.sleep(delay_seconds)
        except Exception as e:
            logging.warning(f"Unexpected error on MongoDB attempt {attempt}/{max_retries}: {e}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not connect to MongoDB after {max_retries} attempts")

# Environment-based URIs
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:password@localhost:27017/?authSource=admin')
client = get_mongo_client_with_retry(mongodb_uri)
db = client['scraper_db']
articles_collection = db['articles']

# Selenium setup
# remote_url = os.getenv('SELENIUM_REMOTE_URL', 'http://selenium:4444/wd/hub')
# options = Options()
# options.add_argument("--headless")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

# Instantiate Remote WebDriver using options
# try:
#     driver = Remote(command_executor=remote_url, options=options)
#     logging.info("Selenium Remote WebDriver initialized")
# except Exception as e:
#     logging.error(f"Error initializing Selenium Remote WebDriver: {e}")
#     raise

sports_list = [
    '/pilka-nozna',
    '/436306/tenis',
    '/siatkowka',
    '/609220/lekkoatletyka',
    '/436313/koszykowka',
    '/436301/pilka-reczna'
]

def get_urls(root_url, sport):
    try:
        driver.get(root_url + sport)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        outers = soup.find_all('section', class_='box-one-two-and-list boxes-section')
        links = []
        for outer in outers:
            for link in outer.find_all('a', href=True):
                full = urljoin(root_url, link['href'])
                links.append(full)
                logging.info(f'Scrapped link: {full}')
        return links
    except Exception as e:
        logging.error(f"Error fetching URLs for sport {sport}: {e}")
        return []

def get_article(url):
    try:
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('h1', class_='news-heading__title')
        text_tag = soup.find('div', class_='news__container')
        if not title_tag or not text_tag:
            logging.error(f'Error getting title or text for URL: {url}')
            return {'title': None, 'text': None, 'url': url}
        article = {
            'title': title_tag.text.strip(),
            'text': text_tag.text.strip(),
            'url': url,
            'scraped_at': datetime.utcnow()
        }
        logging.info(f'Success scrapping {url}: "{article["title"]}"')
        return article
    except Exception as e:
        logging.error(f"Exception in get_article for {url}: {e}")
        return {'title': None, 'text': None, 'url': url}

def save_article(article):
    if not article['title'] or not article['text']:
        logging.error(f'Cannot insert null article: {article.get("url")}')
        return
    url = article['url']
    try:
        if not articles_collection.find_one({'url': url}):
            articles_collection.insert_one(article)
            logging.info(f'Stored article "{article["title"]}" in MongoDB')
        else:
            logging.info(f'Article already exists: {url}')
    except Exception as e:
        logging.error(f'Error storing article in MongoDB: {e}')

def scrap():
    root_url = 'https://sport.tvp.pl'
    for sport in sports_list:
        urls = get_urls(root_url, sport)
        for url in urls:
            article = get_article(url)
            save_article(article)

if __name__ == "__main__":
    scrap()
    driver.quit()
    client.close()
