import json
import difflib
import io
from typing import List, Dict, Any

import streamlit as st
from html import escape
def pretty_text_from_input(raw: str) -> str:
    if not raw or not raw.strip():
        return ""
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        return raw.strip()


def compute_unified_lines(old_text: str, new_text: str) -> List[Dict[str, Any]]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    sm = difflib.SequenceMatcher(None, old_lines, new_lines)
    old_num = 1
    new_num = 1
    out: List[Dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                line = old_lines[i1 + k]
                out.append({
                    'text': line,
                    'oldNum': old_num,
                    'newNum': new_num,
                })
                old_num += 1
                new_num += 1

        elif tag == 'replace':
            # deletions
            for k in range(i2 - i1):
                line = old_lines[i1 + k]
                out.append({
                    'text': line,
                    'removed': True,
                    'oldNum': old_num,
                    'newNum': ' ',
                })
                old_num += 1
            # additions
            for k in range(j2 - j1):
                line = new_lines[j1 + k]
                out.append({
                    'text': line,
                    'added': True,
                    'oldNum': ' ',
                    'newNum': new_num,
                })
                new_num += 1

        elif tag == 'delete':
            for k in range(i2 - i1):
                line = old_lines[i1 + k]
                out.append({
                    'text': line,
                    'removed': True,
                    'oldNum': old_num,
                    'newNum': ' ',
                })
                old_num += 1

        elif tag == 'insert':
            for k in range(j2 - j1):
                line = new_lines[j1 + k]
                out.append({
                    'text': line,
                    'added': True,
                    'oldNum': ' ',
                    'newNum': new_num,
                })
                new_num += 1

    return out


def compute_split_view(old_text: str, new_text: str) -> List[Dict[str, Any]]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    sm = difflib.SequenceMatcher(None, old_lines, new_lines)

    result: List[Dict[str, Any]] = []
    old_num = 1
    new_num = 1

    ops = sm.get_opcodes()
    i = 0
    while i < len(ops):
        tag, i1, i2, j1, j2 = ops[i]
        if tag == 'equal':
            for k in range(i2 - i1):
                line = old_lines[i1 + k]
                result.append({
                    'left': {'num': old_num, 'text': line, 'type': 'normal'},
                    'right': {'num': new_num, 'text': line, 'type': 'normal'},
                })
                old_num += 1
                new_num += 1
            i += 1
        else:
            # gather consecutive changed blocks
            left_buf = []
            right_buf = []
            while i < len(ops) and ops[i][0] in ('replace', 'delete', 'insert'):
                tag2, a1, a2, b1, b2 = ops[i]
                if tag2 in ('replace', 'delete'):
                    for k in range(a1, a2):
                        left_buf.append(old_lines[k])
                if tag2 in ('replace', 'insert'):
                    for k in range(b1, b2):
                        right_buf.append(new_lines[k])
                i += 1

            maxlen = max(len(left_buf), len(right_buf))
            for k in range(maxlen):
                if k < len(left_buf):
                    left = {'num': old_num, 'text': left_buf[k], 'type': 'removed'}
                    old_num += 1
                else:
                    left = {'num': ' ', 'text': '', 'type': 'placeholder'}

                if k < len(right_buf):
                    right = {'num': new_num, 'text': right_buf[k], 'type': 'added'}
                    new_num += 1
                else:
                    right = {'num': ' ', 'text': '', 'type': 'placeholder'}

                result.append({'left': left, 'right': right})

    return result


def fold_lines_unified(lines: List[Dict[str, Any]], context_size: int = 3, show_all: bool = False) -> List[Dict[str, Any]]:
    if show_all or len(lines) <= 15:
        return [dict(l, is_fold_marker=False) for l in lines]

    total = len(lines)
    visible = [False] * total
    for i, ln in enumerate(lines):
        if ln.get('added') or ln.get('removed'):
            start = max(0, i - context_size)
            end = min(total - 1, i + context_size)
            for j in range(start, end + 1):
                visible[j] = True

    out: List[Dict[str, Any]] = []
    in_fold = False
    fold_start = -1
    for i in range(total):
        if visible[i]:
            if in_fold:
                folded_count = i - fold_start
                out.append({'is_fold_marker': True, 'text': f"... 折疊了 {folded_count} 行未變更 ..."})
                in_fold = False
            out.append(dict(lines[i], is_fold_marker=False))
        else:
            if not in_fold:
                in_fold = True
                fold_start = i

    if in_fold:
        folded_count = total - fold_start
        out.append({'is_fold_marker': True, 'text': f"... 折疊了 {folded_count} 行未變更 ..."})

    return out


def fold_lines_split(rows: List[Dict[str, Any]], context_size: int = 3, show_all: bool = False) -> List[Dict[str, Any]]:
    if show_all or len(rows) <= 15:
        return [dict(r, is_fold_marker=False) for r in rows]

    total = len(rows)
    visible = [False] * total
    for i, r in enumerate(rows):
        left_changed = r['left'].get('type') == 'removed'
        right_changed = r['right'].get('type') == 'added'
        if left_changed or right_changed:
            start = max(0, i - context_size)
            end = min(total - 1, i + context_size)
            for j in range(start, end + 1):
                visible[j] = True

    out: List[Dict[str, Any]] = []
    in_fold = False
    fold_start = -1
    for i in range(total):
        if visible[i]:
            if in_fold:
                folded_count = i - fold_start
                out.append({'is_fold_marker': True, 'text': f"... 折疊了 {folded_count} 行未變更 ..."})
                in_fold = False
            out.append(dict(rows[i], is_fold_marker=False))
        else:
            if not in_fold:
                in_fold = True
                fold_start = i

    if in_fold:
        folded_count = total - fold_start
        out.append({'is_fold_marker': True, 'text': f"... 折疊了 {folded_count} 行未變更 ..."})

    return out


def build_diff_text(lines: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    for ln in lines:
        if ln.get('added'):
            buf.write(f"+ {ln.get('text','')}\n")
        elif ln.get('removed'):
            buf.write(f"- {ln.get('text','')}\n")
        else:
            buf.write(f"  {ln.get('text','')}\n")
    return buf.getvalue()


def render_unified_html(lines: List[Dict[str, Any]]) -> str:
    css = (
        "<style>"
        ".gd-container{font-family:monospace;background:#0b0b0d;padding:16px;border-radius:8px;color:#e6eef6;}"
        ".gd-row{display:grid;grid-template-columns:48px 48px 24px 1fr;padding:2px 6px;align-items:start;border-bottom:1px solid rgba(255,255,255,0.02);}"
        ".gd-num{color:#94a3b8;text-align:right;padding-right:8px;font-size:12px;}"
        ".gd-prefix{font-weight:700;text-align:center;width:24px;}"
        ".gd-context{color:#9aa4b2;background:transparent;}"
        ".gd-added{background:rgba(16,185,129,0.06);color:#a7f3d0;}"
        ".gd-removed{background:rgba(239,68,68,0.04);color:#fca5a5;}"
        ".gd-fold{background:#0f1724;color:#7dd3fc;font-style:italic;padding:6px;border-radius:4px;margin:8px 0;text-align:center}" 
        "</style>"
    )

    rows_html: List[str] = [css, '<div class="gd-container">']
    for ln in lines:
        if ln.get('is_fold_marker'):
            rows_html.append(f"<div class=\"gd-fold\">{escape(ln.get('text',''))}</div>")
            continue

        cls = 'gd-context'
        prefix = '&nbsp;'
        if ln.get('added'):
            cls = 'gd-added'
            prefix = '+'
        elif ln.get('removed'):
            cls = 'gd-removed'
            prefix = '-'

        oldn = escape(str(ln.get('oldNum', ' ')))
        newn = escape(str(ln.get('newNum', ' ')))
        text = escape(ln.get('text', '')) or '&nbsp;'

        rows_html.append(
            f"<div class=\"gd-row {cls}\">"
            f"<div class=\"gd-num\">{oldn}</div>"
            f"<div class=\"gd-num\">{newn}</div>"
            f"<div class=\"gd-prefix\">{prefix}</div>"
            f"<div class=\"gd-line\">{text}</div>"
            f"</div>"
        )

    rows_html.append('</div>')
    return '\n'.join(rows_html)


def render_split_html(rows: List[Dict[str, Any]]) -> str:
    css = (
        "<style>"
        ".gs-container{font-family:monospace;background:#0b0b0d;padding:12px;border-radius:8px;color:#e6eef6;}"
        ".gs-grid{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid rgba(255,255,255,0.02);}"
        ".gs-col{padding:6px 8px;border-right:1px solid rgba(255,255,255,0.02);}"
        ".gs-row{display:flex;gap:8px;padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.02);align-items:flex-start;}"
        ".gs-num{width:48px;color:#94a3b8;text-align:right;font-size:12px;padding-right:6px;}"
        ".gs-prefix{width:20px;text-align:center;font-weight:700;}"
        ".gs-added{background:rgba(16,185,129,0.06);color:#a7f3d0;}"
        ".gs-removed{background:rgba(239,68,68,0.04);color:#fca5a5;}"
        ".gs-placeholder{opacity:0.25;color:transparent;}"
        ".gs-fold{background:#0f1724;color:#7dd3fc;font-style:italic;padding:6px;border-radius:4px;margin:8px 0;text-align:center}" 
        "</style>"
    )

    rows_html: List[str] = [css, '<div class="gs-container">', '<div class="gs-grid">']
    # left col start
    left_parts: List[str] = ['<div class="gs-col">']
    right_parts: List[str] = ['<div class="gs-col">']

    for r in rows:
        if r.get('is_fold_marker'):
            left_parts.append(f"<div class=\"gs-fold\">{escape(r.get('text',''))}</div>")
            right_parts.append(f"<div class=\"gs-fold\">{escape(r.get('text',''))}</div>")
            continue

        l = r['left']
        rgt = r['right']

        lcls = 'gs-removed' if l.get('type') == 'removed' else ''
        rcls = 'gs-added' if rgt.get('type') == 'added' else ''

        left_parts.append(
            f"<div class=\"gs-row {lcls}\">"
            f"<div class=\"gs-num\">{escape(str(l.get('num')))}</div>"
            f"<div class=\"gs-prefix\">{'-' if l.get('type')=='removed' else '&nbsp;'}</div>"
            f"<div class=\"gs-text\">{escape(l.get('text',''))}</div>"
            f"</div>"
        )

        right_parts.append(
            f"<div class=\"gs-row {rcls}\">"
            f"<div class=\"gs-num\">{escape(str(rgt.get('num')))}</div>"
            f"<div class=\"gs-prefix\">{'+' if rgt.get('type')=='added' else '&nbsp;'}</div>"
            f"<div class=\"gs-text\">{escape(rgt.get('text',''))}</div>"
            f"</div>"
        )

    left_parts.append('</div>')
    right_parts.append('</div>')

    rows_html.extend(left_parts)
    rows_html.extend(right_parts)
    rows_html.append('</div></div>')
    return '\n'.join(rows_html)

def main():
    st.set_page_config(page_title="Git-style JSON Structural Diff", layout='wide')

    st.title("Git-style JSON Structural Diff")

    # Top segmented toggle for view mode (unified / split)
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'unified'

    button_cols = st.columns([1, 1])
    if button_cols[0].button('單欄 (Unified)'):
        st.session_state.view_mode = 'unified'
    if button_cols[1].button('雙欄 (Split)'):
        st.session_state.view_mode = 'split'

    with st.sidebar:
        st.header("Inputs")
        st.markdown("**Upload files (drag & drop supported)**")
        orig_file = st.file_uploader("Original file", type=['json', 'txt'], key='orig_file')
        merged_file = st.file_uploader("Merged file", type=['json', 'txt'], key='merged_file')

        # Fallback text areas for manual paste; file content (if provided) takes precedence
        original_textarea = st.text_area("Original JSON / text", height=200, key='orig')
        merged_textarea = st.text_area("Merged JSON / text", height=200, key='merged')

        # Read uploaded files if present
        if orig_file is not None:
            try:
                raw_bytes = orig_file.read()
                original_raw = raw_bytes.decode('utf-8')
            except Exception:
                # fallback to text area on error
                original_raw = original_textarea
        else:
            original_raw = original_textarea

        if merged_file is not None:
            try:
                raw_bytes = merged_file.read()
                merged_raw = raw_bytes.decode('utf-8')
            except Exception:
                merged_raw = merged_textarea
        else:
            merged_raw = merged_textarea
        st.markdown("---")
        show_all = st.checkbox("Show full structure (no folding)", value=False)

    old_text = pretty_text_from_input(original_raw)
    new_text = pretty_text_from_input(merged_raw)

    if not old_text and not new_text:
        st.info("暫時無相關數據可供比對。請先在左側填入履歷 JSON 並執行整合。")
        return

    unified = compute_unified_lines(old_text, new_text)
    split = compute_split_view(old_text, new_text)

    view_mode = st.session_state.view_mode

    if view_mode == 'unified':
        visible = fold_lines_unified(unified, context_size=3, show_all=show_all)
        # Stats
        additions = sum(1 for l in unified if l.get('added'))
        deletions = sum(1 for l in unified if l.get('removed'))

        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"**+{additions}** additions   **-{deletions}** deletions")
            st.download_button("Download Diff", data=build_diff_text(unified), file_name='diff.txt')
        with col2:
            html = render_unified_html(visible)
            st.markdown(html, unsafe_allow_html=True)

    else:
        visible = fold_lines_split(split, context_size=3, show_all=show_all)
        additions = sum(1 for r in split if r['right'].get('type') == 'added')
        deletions = sum(1 for r in split if r['left'].get('type') == 'removed')

        st.markdown(f"**+{additions}** additions   **-{deletions}** deletions")
        st.download_button("Download Diff", data=build_diff_text(unified), file_name='diff.txt')

        html = render_split_html(visible)
        st.markdown(html, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
