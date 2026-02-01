import streamlit as st
import time
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(page_title="AI Chat Bot", page_icon="🤖")

# Get API_KEY from environment variables
API_KEY = os.getenv("GEMINI_API_KEY", "")

def call_gemini_api(prompt):
    """Call Gemini 2.5 Flash API for text generation"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{"text": "You are a friendly assistant. Please answer in English."}]
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "System Error: Invalid response")
        else:
            return f"API Error: HTTP {response.status_code}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

st.title("AI Chat Bot")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Please enter your message..."):
    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        if not API_KEY:
            full_response = "Please set your GEMINI_API_KEY in the .env file."
        else:
            full_response = call_gemini_api(prompt)
            
        message_placeholder.markdown(full_response)
    
    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": full_response})