import os
import sys
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import openai
from scrapper.scrapper import MeczykiScrapper

logging.basicConfig(level=logging.INFO)

class MeczykiRAG:
    def __init__(self, openai_api_key):
        self.scraper = MeczykiScrapper()
        self.docs = []
        self.articles = []
        self.doc_vectors = None
        self.vectorizer = TfidfVectorizer(stop_words='english')
        openai.api_key = openai_api_key

    def load_articles(self):
        logging.info("Scrapping articles...")
        self.scraper.scrap()
        self.articles = self.scraper.get_articles()
        self.docs = [article['text'] for article in self.articles if article['text']]

        if not self.docs:
            logging.error("No documents loaded.")
            return

        self.doc_vectors = self.vectorizer.fit_transform(self.docs)
        logging.info(f"Loaded {len(self.docs)} documents and vectorized them.")

    def query(self, question):
        if self.doc_vectors is None or self.doc_vectors.shape[0] == 0:
            logging.error("No document vectors found. Load articles first.")
            return "No data loaded."

        question_vec = self.vectorizer.transform([question])
        similarities = cosine_similarity(question_vec, self.doc_vectors).flatten()

        best_idx = similarities.argmax()
        best_article = self.articles[best_idx]

        context = best_article['text'][:1000]

        prompt = f"""Używając poniższego kontekstu odpowiedz na pytanie:
Kontekst: {context}

Pytanie: {question}
Odpowiedź:"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return "Wystąpił błąd podczas przetwarzania zapytania."

