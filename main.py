from rag.rag import MeczykiRAG
import os
import sys
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak klucza OPENAI_API_KEY w zmiennych środowiskowych")

    rag = MeczykiRAG(api_key)
    rag.load_articles()

    while True:
        question = input("Zadaj pytanie (lub wpisz 'exit' aby zakończyć): ")
        if question.lower() == "exit":
            break
        answer = rag.query(question)
        print(f"Odpowiedź: {answer}\n")
