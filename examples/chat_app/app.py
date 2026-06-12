import streamlit as st
import os
import time
from datetime import datetime
from openai import OpenAI
import utils

# Set page config
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles for premium look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Ensure sessions directory is initialized
utils.init_sessions_dir()
config = utils.load_config()

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session_id" not in st.session_state:
    # Generate initial session ID
    st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Sidebar
with st.sidebar:
    st.markdown('<div class="main-title" style="font-size:1.8rem;">Chat Options</div>', unsafe_allow_html=True)
    
    # 1. New Chat Button
    if st.button("➕ 開啟新對話", use_container_width=True, type="primary"):
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.rerun()

    # 2. LLM Config
    st.markdown('<div class="sidebar-header">⚙️ 模型設定</div>', unsafe_allow_html=True)
    with st.expander("API & 參數設定", expanded=True):
        api_key = st.text_input(
            "OpenAI API Key",
            value=config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", ""),
            type="password",
            placeholder="sk-..."
        )
        
        base_url = st.text_input(
            "API Base URL",
            value=config.get("openai_base_url") or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            placeholder="https://api.openai.com/v1"
        )
        
        model_name = st.text_input(
            "Model Name",
            value=config.get("openai_model_name") or os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
            placeholder="gpt-4o"
        )

    # 3. Chat History List
    st.markdown('<div class="sidebar-header">📁 歷史對話</div>', unsafe_allow_html=True)
    sessions = utils.list_sessions()
    
    if not sessions:
        st.caption("尚無歷史對話")
    else:
        for s in sessions:
            # Highlight current active session
            btn_type = "primary" if s["id"] == st.session_state.current_session_id else "secondary"
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(s["label"], key=f"session_btn_{s['id']}", use_container_width=True, type=btn_type):
                    st.session_state.current_session_id = s["id"]
                    st.session_state.messages = utils.load_session(s["id"])
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_btn_{s['id']}", use_container_width=True, help="刪除對話紀錄"):
                    utils.delete_session(s["id"])
                    if st.session_state.current_session_id == s["id"]:
                        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state.messages = []
                    st.rerun()
# Main Window
st.markdown('<div class="main-title">AI Chat Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">基於 Streamlit & OpenAI API 實作的對話介面</div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["💬 Chat 對話", "📁 文件管理"])

with tab1:
    # Get available files
    uploaded_files = utils.list_uploaded_files()
    selected_files = st.multiselect(
        "📚 選擇參考文件 (選取的檔案內容將作為上下文併入對話)",
        options=uploaded_files,
        help="勾選後，AI 會讀取檔案內容並根據該內容進行回答"
    )

    # Load existing messages if list is empty but file exists (e.g. initial reload/load click)
    if not st.session_state.messages and st.session_state.current_session_id:
        st.session_state.messages = utils.load_session(st.session_state.current_session_id)

    # Render Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("請輸入您的問題..."):
        # 1. Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Save original message (without context injection) to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        utils.save_session(st.session_state.current_session_id, st.session_state.messages)

        # 2. Generate assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Set up client
                client = OpenAI(
                    api_key=api_key if api_key else "mock-key",
                    base_url=base_url if base_url else None
                )
                
                # Context Injection
                messages_to_send = []
                # Construct history, but for the last user message, we append context if selected
                for m in st.session_state.messages[:-1]:
                    messages_to_send.append({"role": m["role"], "content": m["content"]})
                
                # Check if there are selected files
                if selected_files:
                    context_parts = []
                    for fname in selected_files:
                        fpath = os.path.join(utils.UPLOADS_DIR, fname)
                        content = utils.parse_file_content(fpath)
                        context_parts.append(f"--- 檔案: {fname} ---\n{content}\n")
                    
                    full_context = "\n".join(context_parts)
                    injected_prompt = f"以下是參考資料：\n{full_context}\n請根據這些資料回答問題：{prompt}"
                    messages_to_send.append({"role": "user", "content": injected_prompt})
                else:
                    messages_to_send.append({"role": "user", "content": prompt})
                
                # API Call with streaming
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages_to_send,
                    stream=True,
                )
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # Append & Save
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                utils.save_session(st.session_state.current_session_id, st.session_state.messages)
                
                # Rerun sidebar listing update
                st.rerun()

            except Exception as e:
                st.error(f"呼叫 API 時發生錯誤: {e}")
                if not api_key:
                    st.info("💡 提示：請在側邊欄填寫正確的 OpenAI API Key 與 Base URL。")

with tab2:
    st.markdown('<div class="sidebar-header">📂 上傳新文件</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "選擇檔案 (支援 .pdf, .docx, .txt, .md)", 
        type=['pdf', 'docx', 'txt', 'md'],
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        last_uploaded = st.session_state.get("last_uploaded_file")
        if last_uploaded != uploaded_file.name:
            with st.spinner("檔案上傳中..."):
                saved_path = utils.save_uploaded_file(uploaded_file)
                st.session_state["last_uploaded_file"] = uploaded_file.name
                st.success(f"成功上傳檔案: {uploaded_file.name}")
                time.sleep(1) # short pause to show success
                st.rerun()
    else:
        if "last_uploaded_file" in st.session_state:
            del st.session_state["last_uploaded_file"]
            
    st.markdown('<div class="sidebar-header">📋 已上傳文件列表</div>', unsafe_allow_html=True)
    files = utils.list_uploaded_files()
    if not files:
        st.info("目前沒有已上傳的文件。")
    else:
        for f in files:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.text(f"📄 {f}")
            with col2:
                if st.button("🗑️", key=f"del_file_{f}", help=f"刪除 {f}"):
                    utils.delete_uploaded_file(f)
                    st.success(f"已刪除 {f}")
                    time.sleep(0.5)
                    st.rerun()
