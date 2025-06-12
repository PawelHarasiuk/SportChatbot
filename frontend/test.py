import streamlit as st
import requests


def main():
    st.set_page_config(page_title="Query App", layout="centered")
    st.title("Query App")

    st.markdown(
        "This app sends a POST request to `http://localhost:8000/query` with a JSON payload containing the user's query.")

    # Input for the query
    query = st.text_area("Enter your query:", value="Co tam u lewandowskiego?", height=100)

    if st.button("Send Query"):
        if not query.strip():
            st.warning("Please enter a query before sending.")
        else:
            url = "http://localhost:8000/query"
            payload = {"query": query}
            headers = {"Content-Type": "application/json"}
            try:
                with st.spinner("Sending request..."):
                    response = requests.post(url, json=payload, headers=headers, timeout=10)

                st.write(f"Status Code: {response.status_code}")
                content_type = response.headers.get("Content-Type", "")

                # Display JSON nicely if JSON response
                if "application/json" in content_type:
                    try:
                        st.subheader("Response JSON:")
                        st.json(response.json())
                    except ValueError:
                        st.error("Received invalid JSON response.")
                else:
                    # Display text or other content
                    st.subheader("Response Text:")
                    st.text(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Error sending request: {e}")


if __name__ == "__main__":
    main()
