"""
Agent Conversation Renderer — Streamlit 版
左側：對話介面  右側：展示介面（檔案瀏覽 + 預覽）
"""

import streamlit as st
# import anthropic
import openai
import base64
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

# ── 頁面設定 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent Conversation Renderer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 目錄 ──────────────────────────────────────────────────────
UPLOAD_DIR   = Path("uploads")
GENERATED_DIR = Path("generated")
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

# ── Session state 初始化 ──────────────────────────────────────
def init_state():
    defaults = {
        "messages":        [],        # [{role, content, components}]
        "uploaded_files":  [],        # [{id, name, path, ext, size, ts}]
        "generated_files": [],        # [{id, name, path, ext, ts, prompt}]
        "active_file":     None,      # file id
        "active_stage_tab":"preview", # preview | source | json
        "client":          None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Openai client ──────────────────────────────────────────
def get_client():
    if st.session_state.client is None:
        base_url = st.secrets.get("OPENAI_BASE_URL")
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        if not api_key:
            st.error("請在 `.streamlit/secrets.toml` 設定 `OPENAI_API_KEY`")
            st.stop()
        st.session_state.client = openai.OpenAI(base_url=base_url, api_key=api_key)
    return st.session_state.client

# ── 工具函式 ──────────────────────────────────────────────────
def file_icon(ext: str) -> str:
    return {
        "pdf": "📄", "docx": "📝", "doc": "📝",
        "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️",
        "gif": "🖼️", "webp": "🖼️", "svg": "🖼️",
    }.get(ext.lower(), "📎")

def is_image(ext: str) -> bool:
    return ext.lower() in {"png", "jpg", "jpeg", "gif", "webp", "svg"}

def is_pdf(ext: str) -> bool:
    return ext.lower() == "pdf"

def is_docx(ext: str) -> bool:
    return ext.lower() in {"docx", "doc"}

def save_upload(uploaded) -> dict:
    fid  = str(uuid.uuid4())[:8]
    ext  = Path(uploaded.name).suffix.lstrip(".")
    dest = UPLOAD_DIR / f"{fid}_{uploaded.name}"
    dest.write_bytes(uploaded.getvalue())
    return {
        "id": fid, "name": uploaded.name,
        "path": dest, "ext": ext,
        "size": uploaded.size,
        "ts": datetime.now().strftime("%H:%M"),
        "source": "upload",
    }

def save_generated(name: str, content: bytes, ext: str, prompt: str = "") -> dict:
    fid  = str(uuid.uuid4())[:8]
    dest = GENERATED_DIR / f"{fid}_{name}"
    dest.write_bytes(content)
    return {
        "id": fid, "name": name,
        "path": dest, "ext": ext,
        "ts": datetime.now().strftime("%H:%M"),
        "source": "model", "prompt": prompt,
    }

def file_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()

def find_file(fid: str) -> dict | None:
    all_files = st.session_state.uploaded_files + st.session_state.generated_files
    return next((f for f in all_files if f["id"] == fid), None)

# ── 呼叫 Claude ───────────────────────────────────────────────
def call_claude(user_text: str, attached_file: dict | None = None) -> str:
    client = get_client()
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    content: list = []

    # 附加檔案
    if attached_file:
        p = attached_file["path"]
        ext = attached_file["ext"].lower()
        if is_image(ext):
            mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime,
                            "data": file_b64(p)},
            })
        elif is_pdf(ext):
            content.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf",
                            "data": file_b64(p)},
            })

    content.append({"type": "text", "text": user_text})

    response = client.messages.create(
        model="sonnet",
        max_tokens=2048,
        system=(
            "你是一個 AI agent，在雙欄式介面中運作。"
            "左欄是對話介面，右欄是展示介面（可預覽 HTML、圖片、PDF、DOCX）。"
            "回答時使用繁體中文，語氣專業但親切。"
            "若使用者要求生成文件，在回應最後加上 JSON 區塊，格式如下：\n"
            "```surface-payload\n{\"kind\":\"html\",\"filename\":\"output.html\","
            "\"content\":\"<html>...</html>\"}\n```"
        ),
        messages=history + [{"role": "user", "content": content}],
    )
    return response.content[0].text

def parse_surface_payload(text: str) -> dict | None:
    """從回應中萃取 surface-payload JSON 區塊"""
    import re
    m = re.search(r"```surface-payload\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def strip_payload_block(text: str) -> str:
    import re
    return re.sub(r"```surface-payload\s*\n.*?\n```", "", text, flags=re.DOTALL).strip()

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── 全域 ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

/* 隱藏 Streamlit 預設元素 */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Topbar ── */
.acr-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 22px;
  background: rgba(255,252,245,0.96);
  border-bottom: 1px solid #ddd4c3;
}
.acr-brand { display: flex; align-items: center; gap: 12px; }
.acr-badge {
  width: 36px; height: 36px; border-radius: 11px;
  background: linear-gradient(135deg,#0f766e,#0a5e57);
  color: white; display: grid; place-items: center;
  font-weight: 700; font-size: 14px;
  box-shadow: 0 4px 12px rgba(15,118,110,.3);
}
.acr-title { font-size: 15px; font-weight: 600; letter-spacing: -.02em; color: #1a2424; }
.acr-sub   { font-size: 11px; color: #7a8b8a; margin-top: 2px; }

/* ── 欄位分隔 ── */
.col-divider {
  border-left: 1px solid #ddd4c3;
  padding-left: 0 !important;
}

/* ── 面板標頭 ── */
.panel-hdr {
  padding: 12px 0 8px;
  border-bottom: 1px solid rgba(221,212,195,.5);
  margin-bottom: 10px;
}
.panel-hdr h3 {
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .07em;
  color: #7a8b8a; margin: 0;
}

/* ── 訊息氣泡 ── */
.msg-wrap { display: flex; flex-direction: column; gap: 4px; margin-bottom: 14px; }
.msg-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: #7a8b8a; padding: 0 4px;
}
.msg-label.user { text-align: right; }
.msg-bubble {
  padding: 11px 15px; border-radius: 16px;
  font-size: 13.5px; line-height: 1.65;
  box-shadow: 0 2px 8px rgba(40,30,15,.07);
}
.msg-bubble.user {
  background: #1a2424; color: rgba(255,255,255,.92);
  border-bottom-right-radius: 5px; margin-left: 20px;
}
.msg-bubble.agent {
  background: rgba(255,253,248,.97);
  border: 1px solid #ddd4c3;
  border-bottom-left-radius: 5px; margin-right: 20px;
}

/* ── info-card ── */
.info-card {
  margin-top: 10px; padding: 10px 13px;
  border-radius: 12px; background: #fff8eb;
  border-left: 3px solid #b45309;
  font-size: 12.5px; line-height: 1.6; color: #3d4f4e;
}

/* ── file chip ── */
.file-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 8px;
  background: #f4efe6; border: 1px solid #ddd4c3;
  font-size: 12px; color: #3d4f4e; margin-top: 8px;
}

/* ── sidebar file list ── */
.sb-file {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 8px; border-radius: 10px;
  font-size: 12px; color: #3d4f4e;
  cursor: pointer; border: 1px solid transparent;
  margin-bottom: 3px; transition: all .15s;
}
.sb-file:hover { background: rgba(255,252,248,.9); }
.sb-file.active { background: #faf7f2; border-color: #ddd4c3; font-weight: 500; }
.sb-file .fname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-badge {
  font-size: 10px; padding: 1px 5px; border-radius: 4px;
  background: #d6f0ea; color: #0f766e; font-weight: 600;
}
.sb-divider { height: 1px; background: #ddd4c3; margin: 8px 2px; }

/* ── stage tab bar ── */
.stab-bar { display: flex; gap: 4px; margin-bottom: 12px; }
.stab {
  font-size: 12px; font-weight: 500; padding: 5px 13px;
  border-radius: 8px; border: 1px solid transparent;
  color: #7a8b8a; cursor: pointer;
}
.stab.on { background: #faf7f2; border-color: #ddd4c3; color: #1a2424; }

/* PDF embed */
.pdf-frame { border: none; border-radius: 14px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="acr-topbar">
  <div class="acr-brand">
    <div class="acr-badge">AI</div>
    <div>
      <div class="acr-title">Agent Conversation Renderer</div>
      <div class="acr-sub">聊天室渲染結構化元件，右側舞台顯示完整介面輸出</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 雙欄主佈局
# ══════════════════════════════════════════════════════════════
chat_col, stage_col = st.columns([4, 6], gap="small")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 左欄：對話介面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with chat_col:
    st.markdown('<div class="panel-hdr"><h3>對話流</h3></div>', unsafe_allow_html=True)

    # 訊息列表
    msg_container = st.container(height=520)
    with msg_container:
        for m in st.session_state.messages:
            role   = m["role"]
            label  = "User" if role == "user" else "Agent"
            cls    = role
            bubble_cls = "user" if role == "user" else "agent"

            html  = f'<div class="msg-wrap">'
            html += f'<div class="msg-label {cls}">{label}</div>'
            html += f'<div class="msg-bubble {bubble_cls}">{m["content"]}'

            # info-card
            if m.get("info"):
                html += f'<div class="info-card">{m["info"]}</div>'

            # file chip
            if m.get("file_chip"):
                fc = m["file_chip"]
                html += f'<div class="file-chip">{file_icon(fc["ext"])} {fc["name"]}</div>'

            html += '</div></div>'
            st.markdown(html, unsafe_allow_html=True)

    # ── Composer ──
    with st.form("composer", clear_on_submit=True):
        attached = st.file_uploader(
            "附加檔案（選填）",
            type=["pdf","docx","doc","png","jpg","jpeg","gif","webp","svg"],
            label_visibility="collapsed",
        )
        user_input = st.text_input(
            "輸入指令", placeholder="輸入指令，或上傳檔案後送出…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("⬆ Send", use_container_width=True)

    if submitted and (user_input.strip() or attached):
        # 1. 儲存附加檔案
        attached_meta = None
        if attached:
            attached_meta = save_upload(attached)
            if attached_meta not in st.session_state.uploaded_files:
                st.session_state.uploaded_files.append(attached_meta)
            st.session_state.active_file = attached_meta["id"]

        # 2. 加入 user message
        chip = None
        if attached_meta:
            chip = {"name": attached_meta["name"], "ext": attached_meta["ext"]}

        st.session_state.messages.append({
            "role": "user",
            "content": user_input or f"（已上傳 {attached.name}）",
            "file_chip": chip,
        })

        # 3. 呼叫 Claude
        with st.spinner("Agent 思考中…"):
            raw = call_claude(user_input or "請分析這個檔案", attached_meta)

        # 4. 解析 surface payload
        payload = parse_surface_payload(raw)
        clean   = strip_payload_block(raw)

        agent_msg: dict = {"role": "assistant", "content": clean}

        if payload:
            fname   = payload.get("filename", "output.html")
            ext     = Path(fname).suffix.lstrip(".")
            content = payload.get("content", "").encode()
            gen     = save_generated(fname, content, ext, prompt=user_input)
            st.session_state.generated_files.append(gen)
            st.session_state.active_file = gen["id"]
            agent_msg["info"] = f"✅ 已生成 <strong>{fname}</strong>，已出現在右側展示介面。"
            agent_msg["file_chip"] = {"name": fname, "ext": ext}

        st.session_state.messages.append(agent_msg)
        st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 右欄：展示介面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with stage_col:
    st.markdown('<div class="panel-hdr"><h3>展示介面</h3></div>', unsafe_allow_html=True)

    # stage body: sidebar (file list) + main viewer
    sb_col, main_col = st.columns([2, 5], gap="small")

    # ── Sidebar ──
    with sb_col:
        # 上傳檔案清單
        st.markdown("**上傳的檔案**", help="使用者帶入的素材")

        for f in st.session_state.uploaded_files:
            is_active = st.session_state.active_file == f["id"]
            label = f"{file_icon(f['ext'])} {f['name']}"
            if st.button(label, key=f"ub_{f['id']}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_file = f["id"]
                st.rerun()

        # 上傳新檔案
        new_file = st.file_uploader(
            "新增檔案",
            type=["pdf","docx","doc","png","jpg","jpeg","gif","webp","svg"],
            key="sb_upload",
            label_visibility="collapsed",
        )
        if new_file:
            meta = save_upload(new_file)
            if not any(f["name"] == meta["name"] for f in st.session_state.uploaded_files):
                st.session_state.uploaded_files.append(meta)
                st.session_state.active_file = meta["id"]
                st.rerun()

        st.divider()

        # 模型產出清單
        st.markdown("**模型產出**")
        for f in st.session_state.generated_files:
            is_active = st.session_state.active_file == f["id"]
            label = f"{file_icon(f['ext'])} {f['name']}"
            if st.button(label, key=f"gb_{f['id']}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_file = f["id"]
                st.rerun()

    # ── Main Viewer ──
    with main_col:
        active = find_file(st.session_state.active_file) if st.session_state.active_file else None

        if active is None:
            st.info("從左側選擇檔案，或透過對話要求 Agent 生成內容。")
        else:
            ext  = active["ext"].lower()
            path = Path(active["path"])
            src  = active["source"]

            # Viewer topbar
            badge = "🔵 上傳" if src == "upload" else "🟢 模型產出"
            st.markdown(f"**{file_icon(ext)} {active['name']}** &nbsp; `{badge}` &nbsp; `{active['ts']}`",
                        unsafe_allow_html=True)

            # Tab bar
            tab_preview, tab_source, tab_json = st.tabs(["👁 預覽", "📄 原始碼", "📦 JSON"])

            # ── 預覽 Tab ──
            with tab_preview:
                if is_image(ext):
                    st.image(str(path), use_container_width=True)

                elif is_pdf(ext):
                    b64 = file_b64(path)
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64}" '
                        f'width="100%" height="560" class="pdf-frame"></iframe>',
                        unsafe_allow_html=True,
                    )

                elif is_docx(ext):
                    # 用 python-docx 轉純文字顯示
                    try:
                        from docx import Document
                        doc = Document(str(path))
                        text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
                        st.markdown(text or "_（文件內容為空）_")
                    except ImportError:
                        st.warning("需要安裝 `python-docx` 才能預覽 DOCX：`pip install python-docx`")
                    except Exception as e:
                        st.error(f"無法解析 DOCX：{e}")

                elif ext == "html":
                    html_src = path.read_text(encoding="utf-8", errors="replace")
                    st.components.v1.html(html_src, height=560, scrolling=True)

                else:
                    st.info("此檔案類型暫不支援預覽，請下載後開啟。")

                # 下載按鈕
                st.download_button(
                    f"⬇ 下載 {active['name']}",
                    data=path.read_bytes(),
                    file_name=active["name"],
                    mime="application/octet-stream",
                    use_container_width=True,
                )

            # ── 原始碼 Tab ──
            with tab_source:
                if ext in {"html", "txt", "md", "css", "js", "json"}:
                    src_text = path.read_text(encoding="utf-8", errors="replace")
                    st.code(src_text, language=ext if ext != "md" else "markdown", line_numbers=True)
                else:
                    st.info("此類型不支援原始碼檢視。")

            # ── JSON Payload Tab ──
            with tab_json:
                payload_data = {
                    "surface": {
                        "id":       active["id"],
                        "filename": active["name"],
                        "ext":      active["ext"],
                        "source":   active["source"],
                        "ts":       active["ts"],
                        "path":     str(active["path"]),
                        "size_bytes": path.stat().st_size,
                    }
                }
                st.json(payload_data)
