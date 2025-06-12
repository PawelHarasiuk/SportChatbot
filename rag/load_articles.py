import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# MongoDB connection setup
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:password@localhost:27017/')
client = MongoClient(mongodb_uri, unicode_decode_error_handler='ignore')
db = client['scraper_db']
articles_collection = db['articles']

def load_articles():
    articles = []

    today = datetime.utcnow()
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    try:
        cursor = articles_collection.find(
            {
                'scraped_at': {
                    '$gte': start_of_day,
                    '$lt': end_of_day
                }
            },
            collation={'locale': 'pl'}
        )

        articles = list(cursor)

        # Ensure proper encoding for any string fields
        for article in articles:
            if 'title' in article:
                article['title'] = article['title'].encode('utf-8').decode('utf-8')
            if 'text' in article:
                article['text'] = article['text'].encode('utf-8').decode('utf-8')

        logger.info(f"Total articles loaded from MongoDB: {len(articles)}")

    except Exception as e:
        logger.error(f"Error loading articles from MongoDB: {e}")
        return []

    return articles