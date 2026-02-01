import streamlit as st
import time
import requests
import json
import os
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(page_title="8-Bit Retro Chat", page_icon="👾", layout="centered")

# --- Environment configuration ---
API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Font handling logic ---
# To support Chinese pixel style, it is recommended to download Chinese pixel fonts, such as Zpix or ChillBitmap
# Here we default to two paths; if local files exist, convert to base64
EN_FONT_PATH = "assets/PressStart2P-Regular.ttf"
ZH_FONT_PATH = "assets/zpix.ttf"

def get_base64_font(font_file):
    try:
        if os.path.exists(font_file):
            with open(font_file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except Exception:
        return None
    return None

b64_en = get_base64_font(EN_FONT_PATH)
b64_zh = get_base64_font(ZH_FONT_PATH)

# Custom CSS
# Load local Chinese pixel font if available, otherwise load web English font with fallback fonts
font_face_en = f"""
    @font-face {{
        font-family: 'Press Start 2P';
        src: url(data:font/ttf;base64,{b64_en}) format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
""" if b64_en else "@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');"

font_face_zh = f"""
    @font-face {{
        font-family: 'PixelFontZH';
        src: url(data:font/ttf;base64,{b64_zh}) format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
""" if b64_zh else ""

zh_font_family = "'PixelFontZH'," if b64_zh else ""

st.markdown(f"""
<style>
    {font_face_en}
    {font_face_zh}

    #MainMenu, header, footer, .stAppDeployButton {{visibility: hidden;}}
    
    /* Global font settings: prioritize English pixel font, try local pixel font or fallback for Chinese */
    html, body, [data-testid="stAppViewContainer"], .stApp, p, div, span, input, button, .stChatMessage {{
        font-family: 'Press Start 2P', {zh_font_family} 'Courier New', 'MS Gothic', sans-serif !important;
        background-color: #0c0c0c !important;
        color: #00ff41 !important;
        /* Disable font smoothing for crisp edges */
        font-smooth: never;
        -webkit-font-smoothing: none;
    }}

    /* Pixel style chat box */
    [data-testid="stChatMessage"] {{
        background-color: #1a1a1a !important;
        border: 4px solid #ffffff !important;
        box-shadow: 6px 6px 0px #555555 !important;
        margin-bottom: 15px !important;
        border-radius: 0px !important;
    }}

    [data-testid="stChatMessageContent"] p {{
        font-size: 12px !important;
        line-height: 1.6 !important;
    }}

    /* Pixelated input box */
    [data-testid="stChatInput"] {{
        border: 4px solid #00ff41 !important;
        background-color: #000000 !important;
    }}

    [data-testid="stChatInput"] textarea {{
        background-color: #000000 !important;
        color: #00ff41 !important;
        font-family: 'Press Start 2P', {zh_font_family} sans-serif !important;
    }}

    /* CRT scanlines */
    [data-testid="stAppViewContainer"]::before {{
        content: " ";
        display: block;
        position: fixed;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%), 
                    linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
        z-index: 1000;
        background-size: 100% 4px, 3px 100%;
        pointer-events: none;
    }}
</style>
""", unsafe_allow_html=True)

def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{"text": "你是一個 8-bit 風格的機器人。說話簡短，帶有復古電腦感，使用繁體中文。"}]
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "ERROR")
        return f"HTTP ERROR {response.status_code}"
    except Exception as e:
        return f"CONNECTION ERROR: {str(e)}"

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "SYSTEM ONLINE. 系統已就緒。"}]

st.markdown("<h1 style='text-align: center; color: white; font-size: 24px;'>CHAT-BOT 3000</h1>", unsafe_allow_html=True)

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👾" if message["role"]=="assistant" else "👤"):
        st.markdown(message["content"])

# Input
if prompt := st.chat_input("TYPE COMMAND..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👾"):
        message_placeholder = st.empty()
        message_placeholder.markdown("[ CALCULATING... ]")
        full_response = call_gemini_api(prompt) if API_KEY else "ERROR: NO API KEY."
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("<br><p style='text-align: center; font-size: 8px; color: #555;'>POWERED BY GEMINI 2.5 FLASH</p>", unsafe_allow_html=True)