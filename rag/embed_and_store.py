from langchain.schema import Document
from rag.config import get_vectorstore

def process_articles(articles):
    docs = []
    for article in articles:
        text = article.get("text", "")
        if not text or not text.strip():
            continue
        metadata = {
            "title": article.get("title"),
            "url": article.get("url"),
            "date": article.get("date")
        }
        docs.append(Document(page_content=text, metadata=metadata))
    return docs

def embed_and_store(docs):
    if not docs:
        print("Brak dokumentów do zapisania")
        return
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    vectorstore.persist()
    print(f"Zapisano {len(docs)} dokumentów do wektorowej bazy")
