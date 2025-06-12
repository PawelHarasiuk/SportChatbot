import os
from flask import Flask, request, jsonify
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import traceback
app = Flask(__name__)

# Konfiguracja: pobieramy ścieżkę do wektorowego magazynu i klucz API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY nie jest ustawione w środowisku")

# Ścieżka, w której przechowywana jest baza ChromaDB
# Domyślnie: /app/data/vectorstore/chroma (zgodnie z wolumenem w docker-compose)
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectorstore/chroma")

# Inicjalizacja embeddingów i vectorstore
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(
    persist_directory=VECTORSTORE_DIR,
    embedding_function=embeddings
)

# Inicjalizacja LLM i łańcucha RetrievalQA
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0,model_name="gpt-4o-mini")
qa_chain = RetrievalQA.from_llm(
    llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/query", methods=["POST"])
def query():
    """
    Przyjmuje JSON: {"query": "tekst pytania"}
    Zwraca JSON:
    {
      "answer": "...",
      "sources": [ {metadata artykułu}, ... ]
    }
    """
    data = request.get_json(silent=True)
    if not data or "query" not in data:
        return jsonify({"error": "Proszę podać pole 'query' w body requestu"}), 400

    query_text = data["query"]
    try:

        result = qa_chain({"query": query_text})
        answer = result.get("result")
        docs = result.get("source_documents", [])
        # Zbieramy metadane źródeł
        sources = []
        for doc in docs:
            # metadata to dict, np. {"title": ..., "url": ..., "date": ...}
            sources.append(doc.metadata)
        return jsonify({
            "answer": answer,
            "sources": sources
        }), 200
    except Exception as e:
         # W razie błędu zwracamy kod 500
        print("--- BŁĄD W OBSŁUDZE ZAPYTANIA /query ---")
        traceback.print_exc() # To wydrukuje pełen traceback do logów Dockera!
        print(f"Szczegóły błędu: {e}")
        # W razie błędu zwracamy kod 500
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Uruchamiamy Flask bezpośrednio
    # Host 0.0.0.0, port 5000 (mapowany w docker-compose)
    app.run(host="0.0.0.0", port=5000)
