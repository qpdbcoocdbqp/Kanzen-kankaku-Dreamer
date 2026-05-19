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
        "thinking_stages": [],
        "chat_expanded":   True,   # 新增：對話欄展開狀態
        "stage_expanded":  False,  # 新增：展示欄展開狀態（初始折疊）
        "split_ratio":     25,     # 新增：對話欄占比（25% = 折疊展示欄時的初始狀態）
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
1. 【最重要】你的回應必須是且只能是一個合法的 JSON 物件，從 `{` 開始，到 `}` 結束。絕對禁止在 JSON 前後加任何文字、說明、markdown 包裝或 ``` 符號。
2. 即使使用者的輸入不完整、缺乏上下文或無法執行，你仍然必須回傳 JSON，使用 `info_card`（variant: warning）說明問題，並在 `suggestions` 引導使用者提供更多資訊。
3. 根據問題內容自動選擇最適合的 component 組合
4. 可以在同一個 components 陣列內混用多種類型
5. 繁體中文回答
6. suggestions 提供 2-3 個後續可問的問題
""").strip()

# ══════════════════════════════════════════════════════════════
# 三階段 OpenAI 調用函數
# ══════════════════════════════════════════════════════════════

def call_openai_stage1_text_content(user_text: str, attached_file: dict | None = None) -> dict:
    """Stage 1: 生成純文本內容和建議"""
    client = get_client()
    model  = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)

    system_prompt = textwrap.dedent("""
    你是一個 AI 助手，以繁體中文回答。

    你的任務：
    1. 清楚、準確地回答使用者的問題
    2. 提供 0-2 個相關的後續問題建議

    回傳一個 JSON 物件（只包含 answer 和 suggestions，不包含 components）：
    {
      "answer": "你的回答文字",
      "suggestions": ["建議問題1", "建議問題2"]
    }

    【重要】你的回應必須是合法的 JSON，從 { 開始到 } 結束，無其他文字。
    """).strip()

    history: list[dict] = [{"role": "system", "content": system_prompt}]

    # 構建訊息內容（支持檔案處理）
    msg_content: list = []

    if attached_file:
        p   = attached_file["path"]
        ext = attached_file["ext"].lower()

        if is_image(ext):
            mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
            msg_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{file_b64(p)}"},
            })
            msg_content.append({"type": "text", "text": user_text or "請分析這張圖片。"})
        elif is_pdf(ext):
            txt = pdf_extract_text(p)
            msg_content.append({"type": "text", "text": f"[PDF 內容]\n{txt[:4000]}\n\n{user_text}"})
        elif is_docx(ext):
            txt = docx_extract_text(p)
            msg_content.append({"type": "text", "text": f"[DOCX 內容]\n{txt[:4000]}\n\n{user_text}"})
        elif ext in {"txt", "md"}:
            try:
                file_text = Path(p).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                file_text = f"（檔案讀取失敗：{e}）"
            fname = attached_file.get("name", f"file.{ext}")
            msg_content.append({
                "type": "text",
                "text": f"[{fname} 內容]\n{file_text[:8000]}\n\n{user_text}",
            })
        else:
            fname = attached_file.get("name", f"file.{ext}")
            msg_content.append({
                "type": "text",
                "text": f"（使用者上傳了檔案：{fname}，格式暫不支援解析）\n\n{user_text}",
            })
    else:
        msg_content.append({"type": "text", "text": user_text})

    history.append({"role": "user", "content": msg_content})

    # API call
    resp = client.chat.completions.create(model=model, messages=history, temperature=0.7, max_tokens=2048)
    raw  = resp.choices[0].message.content

    # 清除 ``` 包裝
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # 擷取第一個 { 到最後一個 }
    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "answer": raw[:500] or "（無法生成回答）",
            "suggestions": [],
        }


def call_openai_stage2_component_plan(answer_text: str) -> dict:
    """Stage 2: 決定使用哪些 components"""
    client = get_client()
    model  = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)

    component_types = "markdown, info_card, data_list, step_process, table, stat_grid, code_block, action_group"

    system_prompt = textwrap.dedent(f"""
    你是一個 UI 元件選擇專家。

    根據提供的回答文本，決定使用哪些 component 類型最合適。
    目標是讓回答以視覺化、結構化方式呈現，不要把大部分內容都放進 markdown。

    可用的 component 類型：
    - markdown：一般說明、解釋、段落文字、Mermaid 圖表
    - info_card：重要提示、警告、狀態通知
    - data_list：key-value 對、屬性清單、詳細資訊
    - step_process：操作步驟、流程說明、教學
    - table：比較資料、結構化清單、多欄資訊
    - stat_grid：KPI、數據摘要、指標展示
    - code_block：程式碼、指令、設定檔
    - action_group：建議操作、快速動作清單

    回傳 JSON：
    {{
      "components_to_use": ["info_card", "data_list", "code_block"],
      "component_descriptions": {{
        "info_card": "摘要或關鍵提醒",
        "data_list": "結構化重點",
        "code_block": "程式碼範例"
      }}
    }}

    選型規則：
    1. 優先選 2 到 4 種互補 component。
    2. markdown 只用於前言、結語、短段落補充，不可作為唯一主體，除非內容真的無法結構化。
    3. 如果是教學、操作、流程，優先包含 step_process。
    4. 如果是比較、差異、清單整理，優先包含 table 或 data_list。
    5. 如果有數字、指標、等級、狀態摘要，優先包含 stat_grid 或 info_card。
    6. 如果有程式碼、指令、設定片段，優先包含 code_block。
    7. 如果內容包含明確建議行動，可包含 action_group。

    【重要】回應必須是合法的 JSON，從 {{ 開始到 }} 結束。
    """).strip()

    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"回答文本：\n{answer_text}"},
    ]

    resp = client.chat.completions.create(model=model, messages=history, temperature=0.5, max_tokens=1024)
    raw  = resp.choices[0].message.content

    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    try:
        result = json.loads(raw)
        # 驗證 components_to_use 是有效的類型
        valid_types = {c.lower() for c in component_types.split(", ")}
        result["components_to_use"] = [
            c for c in result.get("components_to_use", [])
            if c.lower() in valid_types
        ]
        if not result["components_to_use"]:
            result["components_to_use"] = ["info_card", "data_list"]
        elif result["components_to_use"] == ["markdown"]:
            result["components_to_use"] = ["info_card", "data_list", "markdown"]
        return result
    except json.JSONDecodeError:
        return {
            "components_to_use": ["info_card", "data_list", "markdown"],
            "component_descriptions": {
                "info_card": "摘要重點",
                "data_list": "結構化資訊",
                "markdown": "補充說明",
            },
        }


def call_openai_stage3_construct(text_content: dict, component_plan: dict) -> dict:
    """Stage 3: 構建最終的 AGUIResponse"""
    client = get_client()
    model  = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)

    answer = text_content.get("answer", "")
    suggestions = text_content.get("suggestions", [])
    components_to_use = component_plan.get("components_to_use", ["markdown"])
    component_descriptions = component_plan.get("component_descriptions", {})

    system_prompt = textwrap.dedent("""
    你是一個 AG-UI 元件構建專家。根據計劃的 component 類型，將文本轉換為結構化 JSON。

    ## 可用 component 類型定義

    ### markdown
    {"type":"markdown","content":"Markdown 格式文字"}
    用於：一般說明、解釋、段落文字。

    ### info_card
    {"type":"info_card","title":"標題","description":"說明文字","variant":"info"}
    variant：info | warning | success | danger

    ### data_list
    {"type":"data_list","title":"標題（選填）","items":[{"label":"欄位","value":"內容"}]}

    ### step_process
    {"type":"step_process","title":"流程標題","steps":[{"title":"步驟1","description":"說明"}]}

    ### table
    {"type":"table","title":"表格標題","headers":["欄1","欄2"],"rows":[["A","B"]]}

    ### stat_grid
    {"type":"stat_grid","title":"統計標題","items":[{"label":"指標","value":"數值","description":"說明（選填）"}]}

    ### code_block
    {"type":"code_block","title":"標題（選填）","language":"python","content":"程式碼"}

    ### action_group
    {"type":"action_group","title":"動作標題","items":[{"label":"動作","action":"action_id","description":"說明"}]}

    ## 回傳格式
    必須回傳 JSON 物件，結構如下：
    {
      "components": [
        ... 一或多個 component 物件 ...
      ],
      "suggestions": ["建議1", "建議2"]
    }

    【重要】
    1. 回應必須是合法的 JSON，從 { 開始到 } 結束，無其他文字。
    2. suggestions 來自原始回答，直接傳入。
    3. 根據計劃的 component 類型構建 components 陣列。
    4. 優先使用結構化、可視化元件，不要把主要內容都塞進 markdown。
    5. 若答案含有步驟，轉成 step_process。
    6. 若答案含有重點整理、屬性、條件、注意事項，轉成 data_list 或 info_card。
    7. 若答案含有比較、分類、欄位整理，轉成 table。
    8. 若答案含有數值、統計、狀態摘要，轉成 stat_grid。
    9. markdown 最多只作為少量補充段落，避免單一 markdown component 承載全部內容。
    10. 繁體中文內容。
    """).strip()

    components_str = ", ".join(components_to_use)
    descriptions_str = "\n".join([f"- {k}: {v}" for k, v in component_descriptions.items()])

    user_message = f"""請根據以下計劃構建 AG-UI 回應：

計劃的 Component 類型：{components_str}

Component 使用指導：
{descriptions_str}

要轉換的答案文本：
{answer}

建議列表（保持不變）：
{json.dumps(suggestions, ensure_ascii=False)}
"""

    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    resp = client.chat.completions.create(model=model, messages=history, temperature=0.5, max_tokens=4096)
    raw  = resp.choices[0].message.content

    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    try:
        result = json.loads(raw)
        # 確保 suggestions 與原始建議一致
        result["suggestions"] = suggestions
        return result
    except json.JSONDecodeError as e:
        return {
            "components": [
                {"type": "markdown", "content": answer}
            ],
            "suggestions": suggestions,
        }

def _extract_code_blocks(text: str) -> tuple[str, list[dict]]:
    code_blocks = []

    def replacer(match):
        language = (match.group(1) or "text").strip() or "text"
        content = match.group(2).strip()
        code_blocks.append({
            "type": "code_block",
            "title": "程式碼範例",
            "language": language,
            "content": content,
        })
        return ""

    cleaned = re.sub(r"```(\w+)?\n(.*?)```", replacer, text, flags=re.DOTALL)
    return cleaned.strip(), code_blocks

def _parse_step_process(text: str) -> dict | None:
    steps = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:\d+[\.\)]\s+)(.+)$", stripped)
        if match:
            content = match.group(1).strip()
            if ":" in content:
                title, desc = content.split(":", 1)
            elif "：" in content:
                title, desc = content.split("：", 1)
            else:
                title, desc = content, ""
            steps.append({"title": title.strip(), "description": desc.strip()})
    if len(steps) >= 2:
        return {"type": "step_process", "title": "操作流程", "steps": steps}
    return None

def _parse_data_list(text: str) -> dict | None:
    items = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-•").strip()
        if not stripped:
            continue
        if ":" in stripped:
            label, value = stripped.split(":", 1)
        elif "：" in stripped:
            label, value = stripped.split("：", 1)
        else:
            continue
        if label.strip() and value.strip():
            items.append({"label": label.strip(), "value": value.strip()})
    if len(items) >= 2:
        return {"type": "data_list", "title": "重點整理", "items": items[:8]}
    return None

def _parse_stat_grid(text: str) -> dict | None:
    items = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-•").strip()
        if not stripped:
            continue
        match = re.match(r"^([^:：]+)[:：]\s*([<>~=]?\s*[\d\.]+%?|[\d\.]+(?:\s*[A-Za-z]+)?)\s*(.*)$", stripped)
        if match:
            items.append({
                "label": match.group(1).strip(),
                "value": match.group(2).strip(),
                "description": match.group(3).strip() or None,
            })
    if 1 <= len(items) <= 4:
        return {"type": "stat_grid", "title": "摘要指標", "items": items}
    return None

def _build_info_card(text: str) -> dict | None:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return None
    first = paragraphs[0]
    variant = "info"
    lowered = first.lower()
    if any(word in first for word in ["注意", "警告", "風險", "錯誤"]):
        variant = "warning"
    elif any(word in first for word in ["可以", "建議", "適合", "成功"]):
        variant = "success"
    return {
        "type": "info_card",
        "title": "重點摘要",
        "description": first[:240],
        "variant": variant,
    }

def _build_markdown_remainder(text: str) -> dict | None:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not cleaned:
        return None
    return {"type": "markdown", "content": cleaned}

def normalize_agui_response(agui_resp: dict, fallback_answer: str) -> dict:
    components = agui_resp.get("components", []) or []
    if not components:
        components = [{"type": "markdown", "content": fallback_answer}]

    non_markdown = [c for c in components if c.get("type") != "markdown"]
    markdown_parts = [
        c.get("content", "").strip()
        for c in components
        if c.get("type") == "markdown" and c.get("content", "").strip()
    ]

    if non_markdown and markdown_parts:
        agui_resp["components"] = components
        return agui_resp

    if non_markdown:
        agui_resp["components"] = components
        return agui_resp

    source_text = "\n\n".join(markdown_parts) or fallback_answer
    text_without_code, code_blocks = _extract_code_blocks(source_text)

    rebuilt = []
    info_card = _build_info_card(text_without_code)
    if info_card:
        rebuilt.append(info_card)

    step_process = _parse_step_process(text_without_code)
    if step_process:
        rebuilt.append(step_process)

    stat_grid = _parse_stat_grid(text_without_code)
    if stat_grid:
        rebuilt.append(stat_grid)

    data_list = _parse_data_list(text_without_code)
    if data_list:
        rebuilt.append(data_list)

    rebuilt.extend(code_blocks)

    markdown_remainder = _build_markdown_remainder(text_without_code)
    if markdown_remainder and len(rebuilt) < 2:
        rebuilt.append(markdown_remainder)
    elif markdown_remainder and not any(c.get("type") == "markdown" for c in rebuilt):
        if len(markdown_remainder["content"]) <= 280:
            rebuilt.append(markdown_remainder)

    agui_resp["components"] = rebuilt or [{"type": "markdown", "content": fallback_answer}]
    return agui_resp


# ══════════════════════════════════════════════════════════════
# 呼叫 OpenAI → AGUIResponse（三階段編排）
# ══════════════════════════════════════════════════════════════
def call_openai(user_text: str, attached_file: dict | None = None, progress_target=None) -> dict:
    """三階段生成 AG-UI 回應：(1) 生成文本 (2) 決定 components (3) 構建最終回應"""
    try:
        st.session_state.thinking_stages = []

        # Stage 1: 生成純文本內容和建議
        st.session_state.thinking_stages.append("📝 Stage 1: 生成內容...")
        if progress_target is not None:
            render_thinking_bubble(progress_target, st.session_state.thinking_stages)
        text_content = call_openai_stage1_text_content(user_text, attached_file)

        # Stage 2: 決定 component 計劃
        st.session_state.thinking_stages.append("🎨 Stage 2: 決定元件類型...")
        if progress_target is not None:
            render_thinking_bubble(progress_target, st.session_state.thinking_stages)
        component_plan = call_openai_stage2_component_plan(text_content.get("answer", ""))

        # Stage 3: 構建最終回應
        st.session_state.thinking_stages.append("🔨 Stage 3: 構建最終回應...")
        if progress_target is not None:
            render_thinking_bubble(progress_target, st.session_state.thinking_stages)
        agui_resp = call_openai_stage3_construct(text_content, component_plan)
        agui_resp = normalize_agui_response(agui_resp, text_content.get("answer", ""))

        # 檢查是否有 surface component
        has_surface = any(c.get("type") == "surface" for c in agui_resp.get("components", []))
        if has_surface:
            if not st.session_state.stage_expanded:
                st.session_state.stage_expanded = True
                st.session_state.split_ratio = 25

        return agui_resp

    except Exception as e:
        st.error(f"生成回應時出錯：{e}")
        return {
            "components": [
                {"type": "info_card", "title": "處理錯誤", "description": f"無法生成回應：{str(e)[:200]}", "variant": "danger"}
            ],
            "suggestions": [],
        }

def pdf_extract_text(path: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages[:10])
    except Exception as e:
        return f"（PDF 解析失敗：{e}）"

def docx_extract_text(path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"（DOCX 解析失敗：{e}）"

# ══════════════════════════════════════════════════════════════
# 渲染 AG-UI 元件
# ══════════════════════════════════════════════════════════════
def render_agui_components(components: list):
    for comp in components:
        t = comp.get("type", "")

        # ── markdown ──
        if t == "markdown":
            st.markdown(comp.get("content", ""))

        # ── info_card ──
        elif t == "info_card":
            variant = comp.get("variant", "info")
            color_map = {"info":"#3498db","warning":"#f39c12","success":"#27ae60","danger":"#e74c3c"}
            bg = color_map.get(variant, "#3498db")
            st.markdown(f"""
<div style="border-left:4px solid {bg}; padding:12px; background:#1e1e1e; margin:8px 0; border-radius:4px;">
  <div style="font-weight:600; font-size:1em; color:{bg};">{comp.get('title','')}</div>
  <div style="margin-top:6px; color:#ddd;">{comp.get('description','')}</div>
</div>""", unsafe_allow_html=True)

        # ── data_list ──
        elif t == "data_list":
            if comp.get("title"):
                st.caption(comp["title"])
            for item in comp.get("items", []):
                lbl = item.get("label","")
                val = item.get("value","")
                with st.container(border=True):
                    left, right = st.columns([1, 3], gap="small")
                    with left:
                        st.markdown(f"**{lbl}**")
                    with right:
                        st.write(val)

        # ── step_process ──
        elif t == "step_process":
            st.markdown(f"### {comp.get('title','流程')}")
            for i, step in enumerate(comp.get("steps",[]), 1):
                title = step.get("title","")
                desc  = step.get("description","")
                with st.container(border=True):
                    ncol, ccol = st.columns([1, 12], gap="small")
                    with ncol:
                        st.markdown(f"**{i}**")
                    with ccol:
                        st.markdown(f"**{title}**")
                        if desc:
                            st.write(desc)

        # ── table ──
        elif t == "table":
            if comp.get("title"):
                st.markdown(f"**{comp['title']}**")
            headers = comp.get("headers", [])
            rows    = comp.get("rows", [])
            if headers and rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=headers)
                st.dataframe(df, use_container_width=True)

        # ── stat_grid ──
        elif t == "stat_grid":
            if comp.get("title"):
                st.markdown(f"**{comp['title']}**")
            items = comp.get("items", [])
            cols  = st.columns(len(items))
            for ci, item in enumerate(items):
                with cols[ci]:
                    st.metric(label=item.get("label",""), value=item.get("value",""),
                              help=item.get("description"))

        # ── code_block ──
        elif t == "code_block":
            if comp.get("title"):
                st.markdown(f"**{comp['title']}**")
            lang = comp.get("language", "python")
            code = comp.get("content", "")
            st.code(code, language=lang)

        # ── action_group ──
        elif t == "action_group":
            st.markdown(f"**{comp.get('title','建議動作')}**")
            items = comp.get("items", [])
            cols = st.columns(len(items)) if items else []
            for idx, item in enumerate(items):
                lbl = item.get("label", "")
                act = item.get("action", "")
                desc = item.get("description", "")
                btn_text = f"{lbl}"
                if desc:
                    btn_text += f" - {desc}"
                with cols[idx]:
                    if st.button(btn_text, key=f"act_{act}_{id(comp)}", use_container_width=True):
                        st.session_state.pending_suggestion = lbl
                        st.rerun()

        # ── surface ──
        elif t == "surface":
            kind  = comp.get("kind", "html")
            title = comp.get("title", "surface")
            if kind == "html":
                html_src = comp.get("html", "")
                css      = comp.get("css", "")
                full     = f"<style>{css}</style>{html_src}"
                fname    = f"{title.replace(' ','_')}.html"
                # 用 prompt（title）去重，避免每次 rerun 重複寫入
                existing = next(
                    (f for f in st.session_state.generated_files
                     if f.get("prompt") == title and f["ext"] == "html"),
                    None,
                )
                if existing is None:
                    meta = save_generated(fname, full.encode("utf-8"), "html", prompt=title)
                    st.session_state.generated_files.append(meta)
                    st.session_state.active_file = meta["id"]
                st.success(f"✅ 已產生 surface：{title}，請至右側展示介面查看。")
            elif kind == "svg":
                svg_src = comp.get("svg", "")
                fname   = f"{title.replace(' ','_')}.svg"
                existing = next(
                    (f for f in st.session_state.generated_files
                     if f.get("prompt") == title and f["ext"] == "svg"),
                    None,
                )
                if existing is None:
                    meta = save_generated(fname, svg_src.encode("utf-8"), "svg", prompt=title)
                    st.session_state.generated_files.append(meta)
                    st.session_state.active_file = meta["id"]
                st.success(f"✅ 已產生 SVG：{title}，請至右側展示介面查看。")
            else:
                st.info(f"surface kind={kind} 暫不支援")

        # ── 未知類型 ──
        else:
            st.warning(f"未知 component type: {t}")

def render_thinking_bubble(target, stage_lines: list[str]):
    stage_html = "".join(
        f'<div style="margin-top:8px;">{line}</div>' for line in stage_lines
    )
    target.markdown(f"""
<div class="msg-meta">Agent</div>
<div class="thinking-bubble">
  <div style="display:flex;align-items:center;">
    <div class="thinking-dot"></div>
    <div class="thinking-dot"></div>
    <div class="thinking-dot"></div>
    <span style="margin-left:4px;">思考中…</span>
  </div>
  <div style="margin-top:6px; width:100%;">{stage_html}</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 自定義 CSS（去除 header）
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* 隱藏 Streamlit header */
header[data-testid="stHeader"] {
    display: none !important;
}

/* 調整主容器頂部間距 */
.main .block-container {
    padding-top: 1rem !important;
}

/* Panel 樣式 */
.panel-hdr {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    margin-bottom: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-hdr h3 {
    margin: 0;
    font-size: 1.1em;
}

/* 訊息氣泡 */
.msg-meta {
    font-size: 0.85em;
    color: #888;
    margin-bottom: 4px;
}

.msg-user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 18px;
    margin-bottom: 12px;
    max-width: 80%;
}

.msg-agent {
    background: #2a2a2a;
    color: #eee;
    padding: 14px 18px;
    border-radius: 18px;
    margin-bottom: 12px;
    border: 1px solid #444;
}

.agent-bubble {
    margin-bottom: 12px;
}

.agent-bubble div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 18px;
    padding: 14px 18px;
}

.file-chip {
    display: inline-flex;
    align-items: center;
    background: rgba(255,255,255,0.2);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.9em;
    margin-top: 6px;
}

.thinking-bubble {
    background: #2a2a2a;
    padding: 12px 18px;
    border-radius: 18px;
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    border: 1px solid #444;
    margin-bottom: 12px;
}

.thinking-dot {
    width: 8px;
    height: 8px;
    background: #667eea;
    border-radius: 50%;
    margin: 0 3px;
    animation: thinking 1.4s infinite ease-in-out both;
}

.thinking-dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes thinking {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.pdf-frame {
    border: 1px solid #444;
    border-radius: 8px;
}

/* 折疊按鈕樣式 */
.toggle-btn {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
    padding: 4px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    transition: all 0.2s;
}

.toggle-btn:hover {
    background: rgba(255,255,255,0.2);
}

/* 拖動手柄樣式 */
.resize-handle {
    width: 8px;
    background: #444;
    cursor: col-resize;
    position: relative;
    transition: background 0.2s;
}

.resize-handle:hover {
    background: #667eea;
}

.resize-handle::before {
    content: '⋮';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #888;
    font-size: 1.2em;
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主版面配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 根據展開狀態計算列寬比例
if not st.session_state.chat_expanded and not st.session_state.stage_expanded:
    # 兩邊都折疊：顯示小寬度（各占 50%）
    col_widths = [1, 1]
elif not st.session_state.chat_expanded:
    # 對話欄折疊，展示欄展開
    col_widths = [1, 9]
elif not st.session_state.stage_expanded:
    # 對話欄展開，展示欄折疊
    col_widths = [9, 1]
else:
    # 兩邊都展開：使用自定義比例
    chat_ratio = st.session_state.split_ratio
    stage_ratio = 100 - chat_ratio
    col_widths = [chat_ratio, stage_ratio]

chat_col, stage_col = st.columns(col_widths, gap="small")
thinking_placeholder = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 左欄：對話流
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with chat_col:
    # Panel Header with Toggle Button
    toggle_label = "◀" if st.session_state.chat_expanded else "▶"
    
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown('<div class="panel-hdr"><h3>對話流</h3></div>', unsafe_allow_html=True)
    with col_btn:
        if st.button(toggle_label, key="chat_toggle", help="展開/折疊對話欄"):
            st.session_state.chat_expanded = not st.session_state.chat_expanded
            st.rerun()

    if st.session_state.chat_expanded:
        # ── 對話欄內容 ──
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # ── 訊息串 ──
        for i, m in enumerate(st.session_state.messages):
            if m["role"] == "user":
                st.markdown('<div class="msg-meta">User</div>', unsafe_allow_html=True)
                content_text = m.get("content", "")
                chip = m.get("file_chip")
                chip_html = ""
                if chip:
                    chip_html = f'<div class="file-chip">{file_icon(chip["ext"])} {chip["name"]}</div>'
                st.markdown(
                    f'<div class="msg-user">{content_text}{chip_html}</div>',
                    unsafe_allow_html=True,
                )

            else:
                st.markdown('<div class="msg-meta">Agent</div>', unsafe_allow_html=True)
                st.markdown('<div class="agent-bubble">', unsafe_allow_html=True)
                with st.container(border=True):
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
        thinking_placeholder = st.empty()
        if st.session_state.thinking:
            render_thinking_bubble(thinking_placeholder, st.session_state.get("thinking_stages", []))

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Composer ──
        # pending_suggestion 在 form 外先讀取，避免 clear_on_submit 清掉它
        prefill = st.session_state.get("pending_suggestion", "")
        with st.form("composer", clear_on_submit=True):
            attached = st.file_uploader(
                "附加檔案",
                type=["pdf","docx","doc","png","jpg","jpeg","gif","webp","txt","md"],
                label_visibility="collapsed",
            )
            user_input = st.text_input(
                "輸入指令", value=prefill,
                placeholder="輸入指令，或上傳檔案後送出…",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("⬆ Send", use_container_width=True)

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
            st.session_state.thinking_stages = []
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
        progress_target=thinking_placeholder,
    )

    st.session_state.messages.append({
        "role": "assistant",
        "agui": agui_resp,
    })
    st.session_state.thinking = False
    st.session_state.thinking_stages = []
    st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 右欄：展示介面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with stage_col:
    # Panel Header with Toggle Button and Resize Slider
    toggle_label = "▶" if st.session_state.stage_expanded else "◀"
    
    col_title2, col_btn2 = st.columns([4, 1])
    with col_title2:
        st.markdown('<div class="panel-hdr"><h3>展示介面</h3></div>', unsafe_allow_html=True)
    with col_btn2:
        if st.button(toggle_label, key="stage_toggle", help="展開/折疊展示欄"):
            st.session_state.stage_expanded = not st.session_state.stage_expanded
            st.rerun()

    if st.session_state.stage_expanded:
        # 比例調整滑桿（只有當兩邊都展開時才顯示）
        if st.session_state.chat_expanded:
            st.markdown("##### 調整畫面比例")
            new_ratio = st.slider(
                "對話欄占比 (%)",
                min_value=10,
                max_value=90,
                value=st.session_state.split_ratio,
                step=5,
                key="ratio_slider",
                label_visibility="collapsed"
            )
            if new_ratio != st.session_state.split_ratio:
                st.session_state.split_ratio = new_ratio
                st.rerun()

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
    else:
        # 展示欄折疊時顯示提示
        st.info("展示欄已折疊，點擊上方按鈕展開")
