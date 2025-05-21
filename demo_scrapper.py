from scrapper import MeczykiScrapper

scrapper = MeczykiScrapper()
scrapper.scrap()
articles = scrapper.get_articles()

for article in articles:
    print(article)