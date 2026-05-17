"""
Agent Conversation Renderer — Streamlit 版（OpenAI）
AG-UI Protocol：模型回傳結構化 JSON，在聊天泡泡內渲染對應元件
"""

import os
import re
import json
import uuid
import base64
import textwrap
from pathlib import Path
from datetime import datetime

import streamlit as st
import openai

# ══════════════════════════════════════════════════════════════
# 頁面設定
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Agent Conversation Renderer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

UPLOAD_DIR    = Path("uploads")
GENERATED_DIR = Path("generated")
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

DEFAULT_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-3.5")

# ══════════════════════════════════════════════════════════════
# Session state
# ══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "messages":        [],   # [{role, content?, agui?, file_chip?}]
        "uploaded_files":  [],
        "generated_files": [],
        "active_file":     None,
        "thinking":        False,
        "client":          None,
        "pending_suggestion": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════
# OpenAI client
# ══════════════════════════════════════════════════════════════
def get_client() -> openai.OpenAI:
    if st.session_state.client is None:
        api_key  = st.secrets.get("OPENAI_API_KEY", "")
        base_url = st.secrets.get("OPENAI_BASE_URL", None)
        if not api_key:
            st.error("請在 `.streamlit/secrets.toml` 設定 `OPENAI_API_KEY`")
            st.stop()
        st.session_state.client = openai.OpenAI(api_key=api_key, base_url=base_url)
    return st.session_state.client

# ══════════════════════════════════════════════════════════════
# 檔案工具
# ══════════════════════════════════════════════════════════════
def file_icon(ext: str) -> str:
    return {"pdf":"📄","docx":"📝","doc":"📝","png":"🖼️","jpg":"🖼️",
            "jpeg":"🖼️","gif":"🖼️","webp":"🖼️","svg":"🖼️"}.get(ext.lower(),"📎")

def is_image(ext): return ext.lower() in {"png","jpg","jpeg","gif","webp"}
def is_pdf(ext):   return ext.lower() == "pdf"
def is_docx(ext):  return ext.lower() in {"docx","doc"}

def file_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()

def save_upload(up) -> dict:
    fid  = str(uuid.uuid4())[:8]
    ext  = Path(up.name).suffix.lstrip(".")
    dest = UPLOAD_DIR / f"{fid}_{up.name}"
    dest.write_bytes(up.getvalue())
    return {"id":fid,"name":up.name,"path":dest,"ext":ext,
            "size":up.size,"ts":datetime.now().strftime("%H:%M"),"source":"upload"}

def save_generated(name, content_bytes, ext, prompt="") -> dict:
    fid  = str(uuid.uuid4())[:8]
    dest = GENERATED_DIR / f"{fid}_{name}"
    dest.write_bytes(content_bytes)
    return {"id":fid,"name":name,"path":dest,"ext":ext,
            "ts":datetime.now().strftime("%H:%M"),"source":"model","prompt":prompt}

def find_file(fid) -> dict | None:
    return next((f for f in st.session_state.uploaded_files +
                 st.session_state.generated_files if f["id"] == fid), None)

# ══════════════════════════════════════════════════════════════
# AG-UI System Prompt
# ══════════════════════════════════════════════════════════════
AGUI_SYSTEM = textwrap.dedent("""
你是一個 AI agent，在雙欄式介面運作。回答時必須回傳一個 JSON，格式嚴格符合 AGUIResponse。

## AGUIResponse 格式
```json
{
  "components": [ ...一或多個 component... ],
  "suggestions": ["下一個問題1", "下一個問題2"]
}
```

## 可用 component 類型（從中選最適合的）

### markdown
```json
{"type":"markdown","content":"Markdown 格式文字"}
```
用於：一般說明、解釋、段落文字。

### info_card
```json
{"type":"info_card","title":"標題","description":"說明文字","variant":"info"}
```
variant 可選：info | warning | success | danger
用於：重要提示、警告、狀態通知。

### data_list
```json
{"type":"data_list","title":"標題（選填）","items":[{"label":"欄位","value":"內容"}]}
```
用於：key-value 對、屬性清單、詳細資訊。

### step_process
```json
{"type":"step_process","title":"流程標題","steps":[{"title":"步驟1","description":"說明"}]}
```
用於：操作步驟、流程說明、教學。

### table
```json
{"type":"table","title":"表格標題","headers":["欄1","欄2"],"rows":[["A","B"]]}
```
用於：比較資料、結構化清單、多欄資訊。

### stat_grid
```json
{"type":"stat_grid","title":"統計標題","items":[{"label":"指標","value":"數值","description":"說明（選填）"}]}
```
用於：KPI、數據摘要、指標展示。

### code_block
```json
{"type":"code_block","title":"標題（選填）","language":"python","content":"程式碼內容"}
```
用於：程式碼、指令、設定檔。

### action_group
```json
{"type":"action_group","title":"動作標題","items":[{"label":"動作名稱","action":"action_id","description":"說明（選填）"}]}
```
用於：建議操作、快速動作清單。

### surface
```json
{"type":"surface","kind":"html","html":"<html>...</html>","css":"body{}","title":"標題"}
```
kind 可選：html | svg | markdown | iframe
用於：生成完整 HTML 應用介面、SVG 圖表、需要展示在右側舞台的大型內容。
若包含 surface component，它會自動顯示在右側展示介面。

## 規則
1. 必須只回傳 JSON，不加任何說明文字、markdown 包裝或 ```
2. 根據問題內容自動選擇最適合的 component 組合
3. 可以在同一個 components 陣列內混用多種類型
4. 繁體中文回答
5. suggestions 提供 2-3 個後續可問的問題
""").strip()

# ══════════════════════════════════════════════════════════════
# 呼叫 OpenAI → AGUIResponse
# ══════════════════════════════════════════════════════════════
def call_openai(user_text: str, attached_file: dict | None = None) -> dict:
    client = get_client()
    model  = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)

    # 對話歷史（只傳 role/content 字串，agui 欄位不送入）
    history: list[dict] = [{"role": "system", "content": AGUI_SYSTEM}]
    for m in st.session_state.messages:
        role    = m["role"]
        content = m.get("content") or ""
        # agent 回傳的是 agui，用摘要文字代替避免 context 爆炸
        if role == "assistant" and m.get("agui"):
            agui = m["agui"]
            comps = agui.get("components", [])
            summary_parts = []
            for c in comps:
                t = c.get("type", "")
                if t == "markdown":
                    summary_parts.append(c.get("content","")[:200])
                elif t == "info_card":
                    summary_parts.append(f"[{c.get('title','')}] {c.get('description','')[:100]}")
                elif t == "table":
                    summary_parts.append(f"[表格：{c.get('title','')}，{len(c.get('rows',[]))} 列]")
                elif t == "surface":
                    summary_parts.append(f"[已生成 surface：{c.get('title','')}]")
                else:
                    summary_parts.append(f"[{t}]")
            content = " / ".join(summary_parts) or "(agent 回應)"
        history.append({"role": role, "content": content})

    # 本次 user content
    msg_content: list = []

    if attached_file:
        p   = attached_file["path"]
        ext = attached_file["ext"].lower()

        if is_image(ext):
            mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
            msg_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{file_b64(p)}", "detail": "high"},
            })

        elif is_pdf(ext):
            try:
                import pdfplumber
                pages_text = []
                with pdfplumber.open(str(p)) as pdf:
                    for i, page in enumerate(pdf.pages, 1):
                        t = page.extract_text() or ""
                        if t.strip():
                            pages_text.append(f"--- 第 {i} 頁 ---\n{t.strip()}")
                pdf_text = "\n\n".join(pages_text) or "（PDF 無法萃取文字）"
                msg_content.append({"type": "text",
                    "text": f"以下是 PDF《{attached_file['name']}》完整內容：\n\n{pdf_text}"})
            except ImportError:
                msg_content.append({"type":"text","text":"[請安裝 pdfplumber]"})
            except Exception as e:
                msg_content.append({"type":"text","text":f"[PDF 讀取失敗：{e}]"})

        elif is_docx(ext):
            try:
                from docx import Document
                doc  = Document(str(p))
                text = "\n".join(pa.text for pa in doc.paragraphs if pa.text.strip())
                msg_content.append({"type":"text",
                    "text":f"以下是 DOCX《{attached_file['name']}》內容：\n\n{text}"})
            except Exception as e:
                msg_content.append({"type":"text","text":f"[DOCX 解析失敗：{e}]"})

    msg_content.append({"type":"text","text":user_text})
    final_content = msg_content[0]["text"] if (
        len(msg_content) == 1 and msg_content[0]["type"] == "text"
    ) else msg_content

    history.append({"role":"user","content":final_content})

    resp = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=history,
        response_format={"type":"json_object"},
    )
    raw = resp.choices[0].message.content or "{}"

    try:
        return json.loads(raw)
    except Exception:
        # fallback：把原始文字包成 markdown component
        return {
            "components": [{"type":"markdown","content": raw}],
            "suggestions": []
        }

# ══════════════════════════════════════════════════════════════
# AG-UI Streamlit 渲染器
# ══════════════════════════════════════════════════════════════
VARIANT_COLORS = {
    "info":    ("#1d6fa4", "#eef6ff", "ℹ️"),
    "warning": ("#b45309", "#fff8eb", "⚠️"),
    "success": ("#166534", "#f0fdf4", "✅"),
    "danger":  ("#991b1b", "#fff1f2", "🚨"),
}

def render_agui_components(components: list, container=None):
    """把 AGUIComponent list 渲染成 Streamlit widgets。"""
    ctx = container if container else st

    for comp in components:
        t = comp.get("type", "")

        # ── markdown ──────────────────────────────────────────
        if t == "markdown":
            ctx.markdown(comp.get("content",""))

        # ── info_card ─────────────────────────────────────────
        elif t == "info_card":
            variant = comp.get("variant","info")
            color, bg, icon = VARIANT_COLORS.get(variant, VARIANT_COLORS["info"])
            ctx.markdown(f"""
<div style="padding:12px 16px;border-radius:10px;background:{bg};
            border-left:4px solid {color};margin:6px 0;">
  <div style="font-weight:600;color:{color};margin-bottom:4px;">
    {icon} {comp.get('title','')}
  </div>
  <div style="font-size:13.5px;color:#374151;line-height:1.6;">
    {comp.get('description','')}
  </div>
</div>""", unsafe_allow_html=True)

        # ── data_list ─────────────────────────────────────────
        elif t == "data_list":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            rows_html = ""
            for item in comp.get("items", []):
                rows_html += (
                    '<div style="display:grid;grid-template-columns:1fr 1.4fr;gap:8px;' +
                    'padding:8px 12px;border-bottom:1px solid #e0d9cf;background:#ffffff;">' +
                    f'<span style="font-size:12px;color:#374151;font-weight:600;">{item.get("label","")}</span>' +
                    f'<span style="font-size:13px;color:#111827;font-weight:400;">{item.get("value","")}</span>' +
                    '</div>'
                )
            ctx.markdown(
                '<div style="border:1px solid #d5cfc6;border-radius:10px;overflow:hidden;' +
                'margin:6px 0;background:#ffffff;">' + rows_html + '</div>',
                unsafe_allow_html=True,
            )

        # ── step_process ──────────────────────────────────────
        elif t == "step_process":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            steps = comp.get("steps", [])
            steps_html = ""
            for i, step in enumerate(steps, 1):
                connector = "" if i == len(steps) else (
                    '<div style="width:2px;height:20px;background:#d1d5db;'
                    'margin:2px 0 2px 15px;"></div>'
                )
                steps_html += f"""
<div style="display:flex;gap:12px;align-items:flex-start;">
  <div style="width:30px;height:30px;border-radius:50%;background:#0f766e;
              color:white;display:flex;align-items:center;justify-content:center;
              font-size:12px;font-weight:700;flex-shrink:0;">{i}</div>
  <div style="padding-top:4px;">
    <div style="font-size:13.5px;font-weight:600;color:#1a2424;">{step.get('title','')}</div>
    <div style="font-size:12.5px;color:#6b7280;margin-top:2px;line-height:1.5;">
      {step.get('description','')}
    </div>
  </div>
</div>
{connector}"""
            ctx.markdown(f"""
<div style="padding:12px;border:1px solid #e5ddd0;border-radius:10px;
            background:#fdfcf9;margin:6px 0;">
  {steps_html}
</div>""", unsafe_allow_html=True)

        # ── table ─────────────────────────────────────────────
        elif t == "table":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            headers = comp.get("headers", [])
            rows    = comp.get("rows", [])
            if headers:
                header_html = "".join(
                    '<th style="padding:9px 12px;background:#f0ece5;'
                    'font-size:11px;font-weight:700;color:#374151;'
                    'text-transform:uppercase;letter-spacing:.05em;'
                    f'text-align:left;border-bottom:2px solid #d5cfc6;">{h}</th>'
                    for h in headers
                )
                rows_html = ""
                for ri, row in enumerate(rows):
                    bg = "#ffffff" if ri % 2 == 0 else "#f7f4ef"
                    cells = "".join(
                        '<td style="padding:9px 12px;font-size:13px;' +
                        f'color:#111827;border-bottom:1px solid #e8e0d4;">{c}</td>'
                        for c in row
                    )
                    rows_html += f'<tr style="background:{bg};">{cells}</tr>'
                ctx.markdown(f"""
<div style="overflow:auto;border:1px solid #e5ddd0;border-radius:10px;
            overflow:hidden;margin:6px 0;">
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr>{header_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

        # ── stat_grid ─────────────────────────────────────────
        elif t == "stat_grid":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            items = comp.get("items", [])
            cols  = ctx.columns(min(len(items), 3))
            for i, item in enumerate(items):
                with cols[i % len(cols)]:
                    desc = f"<div style='font-size:11px;color:#6b7280;margin-top:3px;'>{item.get('description','')}</div>" if item.get("description") else ""
                    st.markdown(f"""
<div style="padding:14px 16px;border:1px solid #e5ddd0;border-radius:10px;
            background:white;margin:4px 0;">
  <div style="font-size:11px;color:#374151;font-weight:600;margin-bottom:4px;">
    {item.get('label','')}
  </div>
  <div style="font-size:22px;font-weight:700;color:#111827;letter-spacing:-.02em;">
    {item.get('value','')}
  </div>
  {desc}
</div>""", unsafe_allow_html=True)

        # ── code_block ────────────────────────────────────────
        elif t == "code_block":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            lang = comp.get("language","text")
            ctx.code(comp.get("content",""), language=lang)

        # ── action_group ──────────────────────────────────────
        elif t == "action_group":
            if comp.get("title"):
                ctx.markdown(f"**{comp['title']}**")
            for item in comp.get("items", []):
                desc = f" — {item['description']}" if item.get("description") else ""
                ctx.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
            border:1px solid #e5ddd0;border-radius:8px;margin:4px 0;
            background:#fdfcf9;cursor:pointer;">
  <span style="font-size:13px;font-weight:500;color:#0f766e;">
    › {item.get('label','')}
  </span>
  <span style="font-size:12px;color:#6b7280;">{desc}</span>
</div>""", unsafe_allow_html=True)

        # ── surface (渲染到右側展示介面) ───────────────────────
        elif t == "surface":
            kind  = comp.get("kind","html")
            title = comp.get("title","generated-surface")
            fname = re.sub(r"[^\w\-.]", "_", title)

            if kind == "html":
                html_src = comp.get("html","")
                css_src  = comp.get("css","")
                if css_src:
                    html_src = f"<style>{css_src}</style>\n{html_src}"
                if not fname.endswith(".html"):
                    fname += ".html"
                gen = save_generated(fname, html_src.encode(), "html")
                st.session_state.generated_files.append(gen)
                st.session_state.active_file = gen["id"]
                ctx.markdown(f"""
<div style="padding:10px 14px;border-radius:10px;background:#f0fdf4;
            border-left:4px solid #166534;margin:6px 0;font-size:13px;">
  ✅ 已生成 <strong>{fname}</strong>，請查看右側展示介面。
</div>""", unsafe_allow_html=True)

            elif kind == "svg":
                svg_src = comp.get("svg","")
                ctx.markdown(svg_src, unsafe_allow_html=True)

            elif kind == "markdown":
                md_src = comp.get("markdown","")
                if not fname.endswith(".md"):
                    fname += ".md"
                gen = save_generated(fname, md_src.encode(), "md")
                st.session_state.generated_files.append(gen)
                st.session_state.active_file = gen["id"]
                ctx.markdown(md_src)

        else:
            # 未知 component 用 JSON 顯示
            ctx.json(comp)

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

.acr-topbar {
  display:flex; align-items:center; padding:12px 22px;
  background:rgba(255,252,245,.96); border-bottom:1px solid #ddd4c3;
}
.acr-badge {
  width:36px; height:36px; border-radius:11px;
  background:linear-gradient(135deg,#0d5fa0,#0a4880);
  color:white; display:grid; place-items:center;
  font-weight:700; font-size:14px; margin-right:12px;
  box-shadow:0 4px 12px rgba(13,95,160,.3);
}
.acr-title { font-size:15px; font-weight:600; color:#1a2424; }
.acr-sub   { font-size:11px; color:#7a8b8a; }

.panel-hdr { padding:12px 0 8px; border-bottom:1px solid rgba(221,212,195,.5); margin-bottom:10px; }
.panel-hdr h3 { font-size:11px; font-weight:600; text-transform:uppercase;
                letter-spacing:.07em; color:#7a8b8a; margin:0; }

/* ── 訊息 ── */
.msg-meta { font-size:10px; font-weight:700; text-transform:uppercase;
            letter-spacing:.08em; color:#7a8b8a; padding:0 4px; margin-bottom:4px; }
.msg-meta.user-meta { text-align:right; }

.msg-user {
  background:#1a2424; color:rgba(255,255,255,.92);
  border-radius:16px 16px 4px 16px;
  padding:11px 15px; font-size:13.5px; line-height:1.65;
  box-shadow:0 2px 8px rgba(40,30,15,.07);
  margin-left:20px; margin-bottom:14px;
}

.msg-agent {
  background:rgba(255,253,248,.97); color:#1a2424;
  border:1px solid #ddd4c3;
  border-radius:16px 16px 16px 4px;
  padding:14px 16px; margin-right:20px; margin-bottom:14px;
  box-shadow:0 2px 8px rgba(40,30,15,.05);
}

/* ── 思考狀態（在 agent 氣泡內） ── */
.thinking-bubble {
  background:rgba(255,253,248,.97); color:#7a8b8a;
  border:1px dashed #ddd4c3;
  border-radius:16px 16px 16px 4px;
  padding:12px 16px; margin-right:20px; margin-bottom:14px;
  font-size:13px; display:flex; align-items:center; gap:10px;
}
@keyframes pulse { 0%,100%{opacity:.4} 50%{opacity:1} }
.thinking-dot {
  width:6px; height:6px; border-radius:50%; background:#0f766e;
  animation:pulse 1.4s ease infinite;
}
.thinking-dot:nth-child(2){animation-delay:.2s}
.thinking-dot:nth-child(3){animation-delay:.4s}

/* ── file chip ── */
.file-chip {
  display:inline-flex; align-items:center; gap:6px;
  padding:5px 10px; border-radius:8px;
  background:#f4efe6; border:1px solid #ddd4c3;
  font-size:12px; color:#3d4f4e; margin-top:8px;
}

/* ── suggestions ── */
.suggestion-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.suggestion-chip {
  padding:5px 10px; border-radius:999px;
  border:1px solid #d1cbbf; background:#f9f6f1;
  font-size:12px; color:#3d4f4e; cursor:pointer;
  transition:all .15s;
}
.suggestion-chip:hover { background:#e8f5f2; border-color:#0f766e; color:#0f766e; }

.pdf-frame { border:none; border-radius:14px; width:100%; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════
model_display = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)
st.markdown(f"""
<div class="acr-topbar">
  <div class="acr-badge">AI</div>
  <div>
    <div class="acr-title">Agent Conversation Renderer</div>
    <div class="acr-sub">OpenAI · {model_display} · AG-UI Protocol</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 雙欄佈局
# ══════════════════════════════════════════════════════════════
chat_col, stage_col = st.columns([4, 6], gap="small")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 左欄：對話介面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with chat_col:
    st.markdown('<div class="panel-hdr"><h3>對話流</h3></div>', unsafe_allow_html=True)

    msg_container = st.container(height=540)

    with msg_container:
        for m in st.session_state.messages:
            role = m["role"]

            if role == "user":
                # user 氣泡
                st.markdown('<div class="msg-meta user-meta">User</div>', unsafe_allow_html=True)
                chip_html = ""
                if m.get("file_chip"):
                    fc = m["file_chip"]
                    chip_html = f'<div class="file-chip">{file_icon(fc["ext"])} {fc["name"]}</div>'
                st.markdown(
                    f'<div class="msg-user">{m.get("content","")}{chip_html}</div>',
                    unsafe_allow_html=True,
                )

            else:
                # agent 氣泡：用 st.container 包住，讓 widgets 在泡泡內
                st.markdown('<div class="msg-meta">Agent</div>', unsafe_allow_html=True)
                with st.container():
                    st.markdown('<div class="msg-agent">', unsafe_allow_html=True)

                    agui = m.get("agui")
                    if agui:
                        render_agui_components(agui.get("components", []))
                        # suggestions
                        suggestions = agui.get("suggestions", [])
                        if suggestions:
                            st.markdown('<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">', unsafe_allow_html=True)
                            sugg_cols = st.columns(len(suggestions))
                            for si, sugg_text in enumerate(suggestions):
                                with sugg_cols[si]:
                                    if st.button(sugg_text, key=f"sugg_{id(agui)}_{si}",
                                                 use_container_width=True):
                                        st.session_state.pending_suggestion = sugg_text
                                        st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(m.get("content",""))

                    st.markdown('</div>', unsafe_allow_html=True)

        # ── 思考中：在訊息串最下方顯示，在對話框內 ──
        if st.session_state.thinking:
            st.markdown("""
<div class="msg-meta">Agent</div>
<div class="thinking-bubble">
  <div class="thinking-dot"></div>
  <div class="thinking-dot"></div>
  <div class="thinking-dot"></div>
  <span style="margin-left:4px;">思考中…</span>
</div>""", unsafe_allow_html=True)

    # ── Composer ──
    with st.form("composer", clear_on_submit=False):
        attached = st.file_uploader(
            "附加檔案",
            type=["pdf","docx","doc","png","jpg","jpeg","gif","webp","txt","md"],
            label_visibility="collapsed",
        )
        prefill = st.session_state.get("pending_suggestion", "")
        user_input = st.text_input(
            "輸入指令", value=prefill,
            placeholder="輸入指令，或上傳檔案後送出…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("⬆ Send", use_container_width=True)

    # pending_suggestion 在 submitted 後才清，不在渲染階段清
    if submitted and (user_input.strip() or attached):
        final_text = user_input.strip()
        st.session_state.pending_suggestion = ""   # 送出後才清

        # 1. 儲存附件
        attached_meta = None
        if attached:
            attached_meta = save_upload(attached)
            if not any(f["id"] == attached_meta["id"] for f in st.session_state.uploaded_files):
                st.session_state.uploaded_files.append(attached_meta)
            st.session_state.active_file = attached_meta["id"]

        chip = {"name": attached_meta["name"], "ext": attached_meta["ext"]} if attached_meta else None

        # 2. 加入 user 訊息
        st.session_state.messages.append({
            "role": "user",
            "content": final_text or f"（已上傳 {attached.name}）",
            "file_chip": chip,
        })

        # 3. 開啟 thinking 狀態 → rerun 讓氣泡出現
        st.session_state.thinking = True
        st.rerun()

# ── 在 thinking 狀態下執行 API 呼叫 ──
if st.session_state.thinking:
    last_user = next(
        (m for m in reversed(st.session_state.messages) if m["role"] == "user"), None
    )
    attached_meta = find_file(st.session_state.active_file) if st.session_state.active_file else None
    # 只在剛上傳的那次傳入 attached（避免每次 rerun 都重傳）
    is_upload_msg = (
        attached_meta and
        attached_meta.get("source") == "upload" and
        last_user and
        last_user.get("file_chip") and
        last_user["file_chip"]["name"] == attached_meta["name"]
    )

    agui_resp = call_openai(
        last_user["content"] if last_user else "",
        attached_meta if is_upload_msg else None,
    )

    st.session_state.messages.append({
        "role": "assistant",
        "agui": agui_resp,
    })
    st.session_state.thinking = False
    st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 右欄：展示介面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with stage_col:
    st.markdown('<div class="panel-hdr"><h3>展示介面</h3></div>', unsafe_allow_html=True)

    sb_col, main_col = st.columns([2, 5], gap="small")

    # ── Sidebar ──
    with sb_col:
        st.markdown("**上傳的檔案**")
        for f in st.session_state.uploaded_files:
            is_active = st.session_state.active_file == f["id"]
            if st.button(f"{file_icon(f['ext'])} {f['name']}", key=f"ub_{f['id']}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_file = f["id"]
                st.rerun()

        new_file = st.file_uploader(
            "新增",
            type=["pdf","docx","doc","png","jpg","jpeg","gif","webp","txt","md"],
            key="sb_upload", label_visibility="collapsed",
        )
        if new_file:
            meta = save_upload(new_file)
            if not any(f["name"] == meta["name"] for f in st.session_state.uploaded_files):
                st.session_state.uploaded_files.append(meta)
                st.session_state.active_file = meta["id"]
                st.rerun()

        st.divider()

        st.markdown("**模型產出**")
        for f in st.session_state.generated_files:
            is_active = st.session_state.active_file == f["id"]
            if st.button(f"{file_icon(f['ext'])} {f['name']}", key=f"gb_{f['id']}",
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

            badge = "🔵 上傳" if src == "upload" else "🟢 模型產出"
            st.markdown(
                f"**{file_icon(ext)} {active['name']}** &nbsp; `{badge}` &nbsp; `{active['ts']}`",
                unsafe_allow_html=True,
            )

            tab_preview, tab_source, tab_json = st.tabs(["👁 預覽","📄 原始碼","📦 JSON"])

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
                    try:
                        from docx import Document
                        doc  = Document(str(path))
                        text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
                        st.markdown(text or "_（文件內容為空）_")
                    except Exception as e:
                        st.error(f"無法解析 DOCX：{e}")
                elif ext == "html":
                    html_src = path.read_text(encoding="utf-8", errors="replace")
                    st.components.v1.html(html_src, height=560, scrolling=True)
                elif ext in {"md","txt"}:
                    st.markdown(path.read_text(encoding="utf-8", errors="replace"))
                else:
                    st.info("此檔案類型暫不支援預覽，請下載後開啟。")

                st.download_button(
                    f"⬇ 下載 {active['name']}",
                    data=path.read_bytes(),
                    file_name=active["name"],
                    mime="application/octet-stream",
                    use_container_width=True,
                )

            with tab_source:
                if ext in {"html","txt","md","css","js","json","svg"}:
                    src_text = path.read_text(encoding="utf-8", errors="replace")
                    st.code(src_text, language=ext if ext != "md" else "markdown", line_numbers=True)
                else:
                    st.info("此類型不支援原始碼檢視。")

            with tab_json:
                st.json({
                    "surface": {
                        "id":         active["id"],
                        "filename":   active["name"],
                        "ext":        active["ext"],
                        "source":     active["source"],
                        "ts":         active["ts"],
                        "path":       str(active["path"]),
                        "size_bytes": path.stat().st_size,
                    }
                })
