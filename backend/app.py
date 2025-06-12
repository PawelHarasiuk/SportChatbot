import os
from flask import Flask, request, jsonify, json
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY nie jest ustawione w środowisku")

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectorstore/chroma")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(
    persist_directory=VECTORSTORE_DIR,
    embedding_function=embeddings
)

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
    prompt_engineering = 'Napisz wszystko co wiesz na podany temat.'
    data = request.get_json(silent=True)
    if not data or "query" not in data:
        return jsonify({"error": "Proszę podać pole 'query' w body requestu"}), 400

    query_text = data["query"] + " " + prompt_engineering
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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
