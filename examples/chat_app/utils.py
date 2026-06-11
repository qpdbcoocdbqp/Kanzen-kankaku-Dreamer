import os
import json
import yaml
from datetime import datetime

# Define the base directory for sessions relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

def load_config() -> dict:
    """Load configuration from config.yaml if it exists."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}

def init_sessions_dir():
    """Ensure the sessions directory exists."""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

def get_session_path(session_id: str) -> str:
    """Get the full path for a given session ID."""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def save_session(session_id: str, messages: list):
    """Save the chat messages to a JSON file."""
    init_sessions_dir()
    file_path = get_session_path(session_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def load_session(session_id: str) -> list:
    """Load the chat messages from a JSON file. Returns empty list if file doesn't exist."""
    file_path = get_session_path(session_id)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def list_sessions() -> list:
    """
    List all saved sessions sorted by modification time (most recent first).
    Returns list of dicts: [{'id': session_id, 'file': file_name, 'mtime': timestamp, 'label': display_label}]
    """
    init_sessions_dir()
    sessions = []
    for entry in os.listdir(SESSIONS_DIR):
        if entry.endswith(".json"):
            file_path = os.path.join(SESSIONS_DIR, entry)
            session_id = entry[:-5]  # remove .json
            mtime = os.path.getmtime(file_path)
            dt = datetime.fromtimestamp(mtime)
            
            # Read first message to use as label if available
            label = session_id
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    msgs = json.load(f)
                    if msgs and len(msgs) > 0:
                        first_content = msgs[0].get("content", "")
                        # Truncate first message for sidebar label
                        if first_content:
                            label = first_content[:20] + "..." if len(first_content) > 20 else first_content
            except Exception:
                pass
            
            # Format time for display
            display_time = dt.strftime("%m/%d %H:%M")
            sessions.append({
                "id": session_id,
                "file": entry,
                "mtime": mtime,
                "label": f"💬 {label} ({display_time})"
            })
            
    # Sort by mtime descending
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    return sessions

def delete_session(session_id: str):
    """Delete a session's JSON file."""
    file_path = get_session_path(session_id)
    if os.path.exists(file_path):
        os.remove(file_path)
