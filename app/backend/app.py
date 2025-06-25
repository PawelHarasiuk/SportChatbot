import os
from flask import Flask, request, jsonify, json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY nie jest ustawione w środowisku")

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectorstore/chroma")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(
    persist_directory=VECTORSTORE_DIR,
    embedding_function=embeddings
)

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0, model_name="gpt-4o-mini")


qa_template_content = """Jesteś pomocnym asystentem AI, specjalizującym się WYŁĄCZNIE w tematyce sportowej.
Użyj swojej ogólnej wiedzy o sporcie, aby odpowiadać na szerokie pytania i udzielać podstawowych informacji.
Kiedy jednak potrzebujesz informacji o konkretnych wydarzeniach, aktualnościach lub szczegółach, **priorytetowo bazuj na dostarczonych dokumentach sportowych (Kontekst).**
Połącz swoją wiedzę z informacjami z Kontekstu, aby udzielić jak najbardziej kompletnej i trafnej odpowiedzi.

Niezależnie od dokładnego sformułowania pytania o sport (np. "nowinki", "co się ostatnio działo", "aktualności", "opowiedz o"), zawsze staraj się znaleźć i podać najbardziej istotne i dostępne informacje sportowe, wykorzystując zarówno swoją wiedzę, jak i dostarczony kontekst.

Jeśli pytanie użytkownika NIE dotyczy sportu, LUB jeśli mimo interpretacji pytania jako prośby o sportowe informacje (po przeszukaniu zarówno swojej wiedzy, jak i Kontekstu), dostarczone dokumenty sportowe ABOSOLUTNIE NIE zawierają ŻADNYCH RELEWANTNYCH danych, a Twoja wiedza ogólna również nie pozwala na udzielenie satysfakcjonującej odpowiedzi, poinformuj go, że jesteś wyspecjalizowanym asystentem sportowym i nie możesz odpowiedzieć na to pytanie, lub że nie masz wystarczających informacji sportowych na ten temat. Zachowaj uprzejmy ton.
Odpowiadaj zwięźle i na temat, trzymając się ścisłej tematyki sportowej i wykorzystując każdą pasującą informację.

Kontekst:
{context}

Pytanie użytkownika:
{question}

Odpowiedź:"""
QA_PROMPT = PromptTemplate(template=qa_template_content, input_variables=["context", "question"])

qa_chain = RetrievalQA.from_llm(
    llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
    prompt=QA_PROMPT
)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True)
    if not data or "query" not in data:
        return jsonify({"error": "Proszę podać pole 'query' w body requestu"}), 400

    query_text = data["query"]
    
    try:
        result = qa_chain({"query": query_text})
        answer = result.get("result")
        docs = result.get("source_documents", [])
        sources = []
        for doc in docs:
            sources.append(doc.metadata)

        response_data = {
            "answer": answer,
            "sources": sources
        }

        return app.response_class(
            response=json.dumps(response_data, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"Błąd podczas obsługi zapytania: {e}") 
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
