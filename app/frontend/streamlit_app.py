import streamlit as st
import requests
import json
import os


FLASK_BACKEND_URL = os.getenv("FLASK_BACKEND_URL", "http://0.0.0.0:5000") 


st.set_page_config(page_title="SportChatBot", layout="centered")

st.title("🤖 SportChatBot")
st.write("Hej! Jestem tu żeby ułatwić ci dostęp do nowinek z świata sportu. Specjalizuje się w piłce nożnej, koszykówce, piłce ręcznej, siatkówce, tenisie oraz lekkoatletyce.")


if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "chat_placeholders" not in st.session_state:
    st.session_state.chat_placeholders = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

chat_container = st.container()

query = st.chat_input("Zadaj mi pytanie...")


if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Myślę... Proszę czekać..."):
            try:
                response = requests.post(f"{FLASK_BACKEND_URL}/query", json={"query": query})
                response.raise_for_status() 

                result = response.json()
                answer = result.get("answer", "Nie udało mi się znaleźć odpowiedzi.")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except requests.exceptions.ConnectionError:
                st.error("Błąd połączenia z backendem. Upewnij się, że serwer Flask działa.")
                st.session_state.messages.append({"role": "assistant", "content": "Błąd połączenia z backendem."})
            except requests.exceptions.RequestException as e:
                st.error(f"Wystąpił błąd podczas komunikacji z backendem: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Błąd komunikacji: {e}"})
            except json.JSONDecodeError:
                st.error("Backend zwrócił nieprawidłową odpowiedź JSON.")
                st.session_state.messages.append({"role": "assistant", "content": "Błąd: nieprawidłowa odpowiedź JSON."})
            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Nieoczekiwany błąd: {e}"})

