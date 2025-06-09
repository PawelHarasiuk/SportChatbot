import json
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_articles(folder="../articles"):
    articles = []

    if not os.path.exists(folder):
        logger.warning(f"Folder '{folder}' does not exist.")
        return articles

    today = datetime.today().strftime('%Y-%m-%d')

    for fname in os.listdir(folder):
        if fname.endswith(".json"):
            path = os.path.join(folder, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    if fname.startswith(today):
                        data = json.load(f)
                        if isinstance(data, dict):
                            articles.append(data)
                        elif isinstance(data, list):
                            articles.extend(data)
                        logger.info(f"Loaded {len(data) if isinstance(data, list) else 1} articles from {fname}")
                    else:
                        logger.debug(f"Skipping file not from today: {fname}")
            except Exception as e:
                logger.error(f"Could not read file {path}: {e}")

    logger.info(f"Total articles loaded: {len(articles)}")
    return articles