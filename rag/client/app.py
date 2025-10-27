import streamlit as st
import requests
import os
import json


st.set_page_config(page_title="RAG Client", page_icon="🤖")
API_URL = os.getenv("API_URL", "https://7oaty0t2af.execute-api.us-east-1.amazonaws.com")  # Update after deploying stack

st.title("🤖 RAG Client")
st.markdown("A simple client that connects to a Vector database and provides responses")
st.caption("Enter your message below and click 'Send'.")

api_url = st.text_input("API URL", value=API_URL)
prompt = st.text_area("Your search", height=150)

if st.button("Send"):
    if not api_url or not prompt:
        st.error("Please provide both API URL and a prompt.")
    else:
        with st.spinner("Sending request..."):
            try:
                response = requests.post(api_url + "/rag", json={"message": prompt})
                if response.status_code == 200:
                    data = response.json()
                    st.success("Response received:")
                    st.write(data.get("message", "No message in response"))
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")