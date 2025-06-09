import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_embeddings():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY nie ustawione")
    return OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def get_vectorstore(persist_directory="data/vectorstore/chroma"):
    return Chroma(
        embedding_function=get_embeddings(),
        persist_directory=persist_directory
    )
