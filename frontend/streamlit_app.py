"""
Drive Search Assistant — Streamlit Frontend.

A modern, dark-themed chat UI that communicates with the FastAPI backend
to provide conversational Google Drive search.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "120"))

# ═══════════════════════════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Drive Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# Custom CSS — Premium Dark Theme
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    """
<style>
    /* ── Global ─────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.15);
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #a5b4fc !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #c7d2fe !important;
        font-size: 0.9rem;
    }

    /* ── Header ─────────────────────────────────────────────────────── */
    .header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 8px 32px rgba(79, 70, 229, 0.15);
    }

    .header-container h1 {
        color: #e0e7ff;
        font-weight: 700;
        font-size: 1.8rem;
        margin: 0 0 0.5rem 0;
    }

    .header-container p {
        color: #a5b4fc;
        font-size: 1rem;
        margin: 0;
    }

    /* ── Chat messages ──────────────────────────────────────────────── */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 0.8rem !important;
        border: 1px solid rgba(99, 102, 241, 0.08) !important;
    }

    /* ── File card ──────────────────────────────────────────────────── */
    .file-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .file-card:hover {
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.15);
        transform: translateY(-2px);
    }

    .file-card .file-name {
        color: #e0e7ff;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.4rem;
    }

    .file-card .file-meta {
        color: #94a3b8;
        font-size: 0.8rem;
    }

    .file-card a {
        color: #818cf8;
        text-decoration: none;
        font-weight: 500;
    }

    .file-card a:hover {
        color: #a5b4fc;
        text-decoration: underline;
    }

    /* ── Query badge ────────────────────────────────────────────────── */
    .query-badge {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 0.5rem 0 1rem 0;
        font-family: 'Fira Code', 'Cascadia Code', monospace;
        font-size: 0.8rem;
        color: #a5b4fc;
    }

    /* ── Metric cards ───────────────────────────────────────────────── */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }

    .metric-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        flex: 1;
        text-align: center;
    }

    .metric-card .value {
        color: #818cf8;
        font-size: 1.5rem;
        font-weight: 700;
    }

    .metric-card .label {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Status pill ────────────────────────────────────────────────── */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-online {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* ── Scrollbar ──────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* ── Hide Streamlit branding ────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# Session State Initialisation
# ═══════════════════════════════════════════════════════════════════════════

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_searches" not in st.session_state:
    st.session_state.total_searches = 0

if "total_files_found" not in st.session_state:
    st.session_state.total_files_found = 0


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def check_backend_health() -> bool:
    """Check if the FastAPI backend is reachable."""
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def send_message(message: str) -> Dict[str, Any]:
    """Send a chat message to the backend and return the response."""
    payload = {
        "message": message,
        "conversation_id": st.session_state.conversation_id,
    }
    response = httpx.post(
        f"{BACKEND_URL}/api/chat",
        json=payload,
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def clear_conversation() -> None:
    """Clear conversation history on both frontend and backend."""
    try:
        httpx.post(
            f"{BACKEND_URL}/api/clear",
            params={"conversation_id": st.session_state.conversation_id},
            timeout=10,
        )
    except Exception:
        pass
    st.session_state.messages = []
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.total_searches = 0
    st.session_state.total_files_found = 0


def render_file_card(file: Dict[str, Any]) -> str:
    """Render a single file as an HTML card."""
    name = file.get("name", "Untitled")
    mime = file.get("mime_type", "unknown")
    modified = file.get("modified_time", "")
    link = file.get("web_view_link", "")
    size = file.get("size", "")

    # File type icon mapping
    icon_map = {
        "document": "📄",
        "spreadsheet": "📊",
        "presentation": "📽️",
        "pdf": "📕",
        "image": "🖼️",
        "folder": "📁",
        "csv": "📋",
    }
    mime_lower = mime.lower()
    icon = "📄"
    for key, emoji in icon_map.items():
        if key in mime_lower:
            icon = emoji
            break

    # Format modified date
    mod_display = ""
    if modified and modified != "Unknown":
        try:
            dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            mod_display = dt.strftime("%b %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            mod_display = modified

    link_html = ""
    if link and link != "No link available":
        link_html = f'<a href="{link}" target="_blank">Open in Drive ↗</a>'

    size_display = ""
    if size:
        size_display = f' · {size}'

    return f"""
    <div class="file-card">
        <div class="file-name">{icon} {name}</div>
        <div class="file-meta">
            {mime}{size_display}
            {f' · {mod_display}' if mod_display else ''}
            {f' · {link_html}' if link_html else ''}
        </div>
    </div>
    """


# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🔍 Drive Search Assistant")
    st.markdown("---")

    # Backend status
    is_healthy = check_backend_health()
    if is_healthy:
        st.markdown(
            '<span class="status-pill status-online">● Backend Online</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-pill status-offline">● Backend Offline</span>',
            unsafe_allow_html=True,
        )
        st.warning("The backend is not reachable. Make sure it's running.")

    st.markdown("---")

    # Session metrics
    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Searches", st.session_state.total_searches)
    with col2:
        st.metric("Files Found", st.session_state.total_files_found)

    st.markdown("---")

    # New conversation button
    if st.button("🗑️ New Conversation", use_container_width=True):
        clear_conversation()
        st.rerun()

    st.markdown("---")

    # Example queries
    st.markdown("### 💡 Try Asking")
    examples = [
        "Find financial reports from last week",
        "Show me all PDF files",
        "Search for spreadsheets about budget",
        "Find documents modified yesterday",
        "Show me presentations",
        "Search for files containing 'revenue'",
    ]
    for ex in examples:
        if st.button(f"  {ex}", key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_message = ex
            st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#64748b; font-size:0.75rem;'>"
        "Built with LangChain + FastAPI + Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Main Chat Area
# ═══════════════════════════════════════════════════════════════════════════

# Header
st.markdown(
    """
    <div class="header-container">
        <h1>🔍 Drive Search Assistant</h1>
        <p>Search your Google Drive using natural language. Ask me to find files by name, type, content, or date.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

        # Render file cards if present
        if msg.get("files"):
            for f in msg["files"]:
                st.markdown(render_file_card(f), unsafe_allow_html=True)

        # Render query explanation if present
        if msg.get("query_explanation"):
            st.markdown(
                f'<div class="query-badge">🔎 {msg["query_explanation"]}</div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# Chat Input Handling
# ═══════════════════════════════════════════════════════════════════════════

# Handle pending message from example buttons
pending = st.session_state.pop("pending_message", None)
user_input = st.chat_input("Ask me to find files in your Drive…")

message = pending or user_input

if message:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Process with backend
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Searching Drive…"):
            try:
                data = send_message(message)

                response_text = data.get("response", "Sorry, something went wrong.")
                files = data.get("files", [])
                query_explanation = data.get("query_explanation")

                # Display response text
                st.markdown(response_text)

                # Display file cards
                if files:
                    for f in files:
                        st.markdown(render_file_card(f), unsafe_allow_html=True)

                # Display query explanation
                if query_explanation:
                    st.markdown(
                        f'<div class="query-badge">🔎 {query_explanation}</div>',
                        unsafe_allow_html=True,
                    )

                # Save to session
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                        "files": files,
                        "query_explanation": query_explanation,
                    }
                )

                # Update metrics
                st.session_state.total_searches += 1
                st.session_state.total_files_found += len(files)

            except httpx.ConnectError:
                error_msg = (
                    "⚠️ **Cannot connect to the backend.** "
                    "Make sure the FastAPI server is running on "
                    f"`{BACKEND_URL}`."
                )
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except httpx.HTTPStatusError as exc:
                error_msg = f"⚠️ **Server error:** {exc.response.status_code} — {exc.response.text}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except Exception as exc:
                error_msg = f"⚠️ **Unexpected error:** {str(exc)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
