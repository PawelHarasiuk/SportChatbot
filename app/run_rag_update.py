from rag.load_articles import load_articles
from rag.embed_and_store import process_articles, embed_and_store

def main():
    articles = load_articles()
    docs = process_articles(articles)
    if docs:
        embed_and_store(docs)
        print(f"Zapisano {len(docs)} dokumentów do wektorowej bazy.")
    else:
        print("Brak nowych dokumentów do przetworzenia.")

if __name__ == "__main__":
    main()
