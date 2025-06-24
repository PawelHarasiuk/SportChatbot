from urllib.parse import urljoin
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
import shutil  # To clean up temp directories
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import os
import logging
import time


logging.basicConfig(
    level=logging.INFO,  # Changed to INFO for less verbose default output
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_driver():
    """Initialize Selenium WebDriver"""
    remote_url = os.getenv('SELENIUM_REMOTE_URL', 'http://selenium:4444/wd/hub')

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities['goog:chromeOptions'] = options.to_capabilities()['goog:chromeOptions']

    # Add retry logic for connecting to Selenium
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            driver = webdriver.Remote(
                command_executor=remote_url,
                options=options,
            )
            return driver
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            logging.warning(f"Attempt {attempt + 1} failed to connect to Selenium. Retrying... Error: {e}")
            time.sleep(5)
    return None


def get_mongo_client_with_retry(uri, max_retries=10, delay_seconds=3):
    """
    Establishes a connection to MongoDB with retry logic.
    """
    for attempt in range(1, max_retries + 1):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # The 'ping' command is a lightweight way to check if the server is available
            client.admin.command('ping')
            logging.info("Successfully connected to MongoDB.")
            return client
        except ServerSelectionTimeoutError as e:
            logging.warning(
                f"MongoDB connection attempt {attempt}/{max_retries} failed (ServerSelectionTimeoutError): {e}")
            time.sleep(delay_seconds)
        except Exception as e:
            logging.warning(f"Unexpected error on MongoDB connection attempt {attempt}/{max_retries}: {e}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not connect to MongoDB after {max_retries} attempts.")


# Initialize MongoDB client
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:password@localhost:27017/?authSource=admin')
client = get_mongo_client_with_retry(mongodb_uri)
db = client['scraper_db']
articles_collection = db['articles']

# List of sports paths to scrape
sports_list = [
    '/pilka-nozna',
    '/436306/tenis',
    '/siatkowka',
    '/609220/lekkoatletyka',
    '/436313/koszykowka',
    '/436301/pilka-reczna'
]


def get_urls(driver_instance, root_url, sport):
    """
    Fetches article URLs from a given sport section using the provided Selenium driver instance.
    Raises WebDriverException (including InvalidSessionIdException) on Selenium errors.
    """
    target_url = root_url + sport
    logging.info(f"Navigating to {target_url} to extract article URLs...")
    driver_instance.get(target_url)
    html = driver_instance.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find sections containing links to articles
    outers = soup.find_all('section', class_='box-one-two-and-list boxes-section')
    links = []
    for outer in outers:
        for link in outer.find_all('a', href=True):
            full_url = urljoin(root_url, link['href'])
            links.append(full_url)

    logging.info(f"Extracted {len(links)} URLs from {target_url}.")
    return links


def get_article(driver_instance, url):
    """
    Fetches an article's title and text content from a given URL
    using the provided Selenium driver instance.
    Raises WebDriverException (including InvalidSessionIdException) on Selenium errors.
    """
    logging.info(f"Navigating to {url} to scrape article content...")
    driver_instance.get(url)
    html = driver_instance.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Locate article title and text elements based on their CSS classes
    title_tag = soup.find('h1', class_='news-heading__title')
    text_tag = soup.find('div', class_='news__container')

    if not title_tag or not text_tag:
        logging.warning(f'Could not find expected title or text content for URL: {url}. Returning partial/empty data.')
        return {'title': None, 'text': None, 'url': url}

    article = {
        'title': title_tag.text.strip(),
        'text': text_tag.text.strip(),
        'url': url,
        'scraped_at': datetime.utcnow()  # Record when the article was scraped
    }
    logging.info(f'Successfully scraped article: "{article["title"]}" from {url}.')
    return article


def save_article(article):
    """
    Saves an article to MongoDB. Checks if the article already exists by URL
    to prevent duplicates.
    """
    if not article or not article.get('title') or not article.get('text'):
        logging.warning(f'Skipping save: Article is empty or incomplete for URL: {article.get("url", "N/A")}')
        return

    url = article['url']
    try:
        # Check if an article with the same URL already exists in the collection
        if not articles_collection.find_one({'url': url}):
            articles_collection.insert_one(article)
            logging.info(f'Stored new article "{article["title"]}" in MongoDB.')
        else:
            logging.info(f'Article already exists for URL: {url}. Skipping insertion.')
    except Exception as e:
        logging.error(f'Error storing article "{url}" in MongoDB: {e}')


def scrap():
    """
    Main scraping function. Manages Selenium driver lifecycle,
    retries operations on session invalidation, and orchestrates
    fetching and saving articles.
    """
    root_url = 'https://sport.tvp.pl'
    driver = None
    temp_profile_dir = None
    # Maximum number of times to retry an operation (including driver re-creation)
    max_operation_retries = 3

    try:
        # Initial driver creation
        driver, temp_profile_dir = create_driver()

        for sport in sports_list:
            urls = []
            # Retry loop for getting URLs for a specific sport section
            for attempt in range(max_operation_retries):
                try:
                    urls = get_urls(driver, root_url, sport)
                    break  # Success, break out of retry loop for URLs
                except (InvalidSessionIdException, WebDriverException) as e:
                    logging.error(
                        f"Selenium error getting URLs for {sport} (attempt {attempt + 1}/{max_operation_retries}): {e}")
                    if attempt < max_operation_retries - 1:
                        logging.warning("Attempting to re-create Selenium driver due to session issue...")
                        # Quit the problematic driver
                        if driver:
                            try:
                                driver.quit()
                            except Exception as quit_e:
                                logging.warning(f"Error quitting old driver before re-creation: {quit_e}")
                        # Clean up the old temporary profile directory
                        if temp_profile_dir and os.path.exists(temp_profile_dir):
                            try:
                                shutil.rmtree(temp_profile_dir)
                            except Exception as dir_e:
                                logging.warning(
                                    f"Error removing old temp profile directory {temp_profile_dir}: {dir_e}")
                        # Create a new driver instance
                        try:
                            driver, temp_profile_dir = create_driver()
                        except Exception as create_e:
                            logging.critical(
                                f"Failed to re-create Selenium driver after {attempt + 1} attempts: {create_e}. Cannot proceed with scraping.")
                            driver = None  # Mark driver as unusable
                            break  # Exit this retry loop if driver re-creation fails
                    else:
                        logging.error(f"Max retries reached for getting URLs for {sport}. Skipping this sport.")
                        urls = []  # Ensure URLs list is empty if all retries failed
                        break  # Exit retry loop, no more retries
                except Exception as e:
                    logging.error(f"Unexpected error getting URLs for sport {sport}: {e}")
                    urls = []
                    break  # Exit retry loop for unexpected errors

            if not urls:
                logging.warning(f"No URLs obtained for sport: {sport}. Moving to next sport.")
                continue

            # Iterate through the extracted URLs and scrape each article
            for url in urls:
                article = {}
                # Retry loop for getting a single article's content
                for attempt in range(max_operation_retries):
                    try:
                        article = get_article(driver, url)
                        break  # Success, break out of retry loop for article
                    except (InvalidSessionIdException, WebDriverException) as e:
                        logging.error(
                            f"Selenium error getting article from {url} (attempt {attempt + 1}/{max_operation_retries}): {e}")
                        if attempt < max_operation_retries - 1:
                            logging.warning(
                                "Attempting to re-create Selenium driver due to session issue for article...")
                            # Quit the problematic driver
                            if driver:
                                try:
                                    driver.quit()
                                except Exception as quit_e:
                                    logging.warning(f"Error quitting old driver for article re-creation: {quit_e}")
                            # Clean up the old temporary profile directory
                            if temp_profile_dir and os.path.exists(temp_profile_dir):
                                try:
                                    shutil.rmtree(temp_profile_dir)
                                except Exception as dir_e:
                                    logging.warning(
                                        f"Error removing old temp profile directory {temp_profile_dir} for article: {dir_e}")
                            # Create a new driver instance
                            try:
                                driver, temp_profile_dir = create_driver()
                            except Exception as create_e:
                                logging.critical(
                                    f"Failed to re-create Selenium driver for article after {attempt + 1} attempts: {create_e}. Skipping article.")
                                driver = None  # Mark driver as unusable
                                break  # Exit this retry loop if driver re-creation fails
                        else:
                            logging.error(f"Max retries reached for getting article from {url}. Skipping this article.")
                            article = {'title': None, 'text': None, 'url': url}  # Ensure article is empty
                            break  # Exit retry loop
                    except Exception as e:
                        logging.error(f"Unexpected error getting article from {url}: {e}")
                        article = {'title': None, 'text': None, 'url': url}
                        break  # Exit retry loop for unexpected errors

                # Save the obtained article (even if it's incomplete due to errors)
                save_article(article)

    except Exception as e:
        logging.critical(f"An unrecoverable error occurred in the main scraping process: {e}", exc_info=True)
    finally:
        # Ensure resources are properly released
        if driver:
            try:
                driver.quit()
                logging.info("Selenium driver quit successfully in finally block.")
            except Exception as e:
                logging.error(f"Error quitting Selenium driver in finally block: {e}")
        if temp_profile_dir and os.path.exists(temp_profile_dir):
            try:
                shutil.rmtree(temp_profile_dir)
                logging.info(f"Removed temporary Chrome user data directory: {temp_profile_dir} in finally block.")
            except Exception as e:
                logging.error(f"Error removing temporary directory {temp_profile_dir} in finally block: {e}")
        if client:
            try:
                client.close()
                logging.info("MongoDB client closed successfully in finally block.")
            except Exception as e:
                logging.error(f"Error closing MongoDB client in finally block: {e}")


if __name__ == "__main__":
    logging.info("[`date`] Starting scraper execution...")
    scrap()
    logging.info("[`date`] Scraper execution finished.")

