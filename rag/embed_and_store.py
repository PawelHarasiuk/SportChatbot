from typing import List, Dict
from langchain.schema import Document
from rag.config import get_vectorstore


def process_articles(articles: List[Dict]) -> List[Document]:
    """Convert articles to Documents for vectorstore."""
    docs = []
    for article in articles:
        text = article.get("text", "")
        if not text or not text.strip():
            continue

        metadata = {
            "title": article.get("title"),
            "url": article.get("url"),
            "date": article.get("date"),
            "source_file": article.get("source_file")
        }
        docs.append(Document(page_content=text, metadata=metadata))
    return docs


def embed_and_store(docs: List[Document], persist_directory: str = "data/vectorstore/chroma"):
    """Embed documents and store them in the vectorstore."""
    if not docs:
        print("No documents to save")
        return

    vectorstore = get_vectorstore(persist_directory)
    vectorstore.add_documents(docs)
    vectorstore.persist()
    print(f"Saved {len(docs)} documents to vector database")
