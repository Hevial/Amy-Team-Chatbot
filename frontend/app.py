"""
Streamlit Frontend for Amy Team Chatbot.

Provides a Gemini-inspired chat interface for users to interact with the
RAG Assistant Coach. Connects to the FastAPI backend for answers and citations.

Design: Dark mode, Inter font, subtle purple accents (Amnesia Esports),
rounded shapes, clean layout inspired by Google Gemini.

Messages are rendered as custom HTML to allow proper right-alignment for
user messages and modern SVG-based avatars — something Streamlit's native
st.chat_message does not support well.
"""

import os
from urllib.parse import urljoin

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_HOST = os.getenv("API_HOST", "http://localhost:8080")
QUERY_ENDPOINT = urljoin(API_HOST, "/query")

# Inline SVG icons for chips (16x16, stroke-based, no emoji)
ICON_BOLT = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
ICON_CLIPBOARD = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/></svg>'
ICON_TROPHY = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 010-5H6"/><path d="M18 9h1.5a2.5 2.5 0 000-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22"/><path d="M18 2H6v7a6 6 0 1012 0V2z"/></svg>'
ICON_TARGET = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
ICON_FILE = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'

SUGGESTION_CHIPS = [
    {"icon": ICON_BOLT, "label": "Disconnection rules", "query": "What is the disconnection rule?"},
    {"icon": ICON_CLIPBOARD, "label": "Latest patch notes", "query": "Summarize the latest patch notes"},
    {"icon": ICON_TROPHY, "label": "Tournament format", "query": "What are the tournament format rules?"},
    {"icon": ICON_TARGET, "label": "Team strategy tips", "query": "What strategic advice can you give based on the current meta?"},
]

# SVG avatars — inline so no external dependencies
AVATAR_AMY = """<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="32" height="32" rx="10" fill="#8B5CF6"/>
<text x="16" y="21" text-anchor="middle" fill="white" font-family="Inter,sans-serif" font-size="14" font-weight="600">A</text>
</svg>"""

AVATAR_USER = """<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="32" height="32" rx="10" fill="#3B3B5C"/>
<circle cx="16" cy="13" r="5" stroke="white" stroke-width="1.5" fill="none"/>
<path d="M8 26c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round"/>
</svg>"""


st.set_page_config(
    page_title="Amy — Assistant Coach",
    page_icon="A",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Design System — CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── Fonts ─────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    *, html, body, [class*="css"], .stMarkdown,
    [data-testid="stChatInput"] textarea,
    p, span, div, h1, h2, h3, label, button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ── Force Uniform Dark Background ────────────────────────────────── */
    .stApp,
    .stApp > div,
    .stApp [data-testid="stAppViewContainer"],
    .stApp [data-testid="stAppViewBlockContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    section[data-testid="stMain"],
    .block-container,
    .main .block-container {
        background-color: #131320 !important;
    }

    /* Nuke any white/light backgrounds */
    .stApp [data-testid="stBottom"],
    .stApp [data-testid="stBottom"] > div {
        background-color: #131320 !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        visibility: hidden !important;
        height: 0 !important;
        position: fixed !important;
    }

    /* ── Sidebar ──────────────────────────────────────────────────────── */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {
        background-color: #16162B !important;
        border-right: 1px solid rgba(139, 92, 246, 0.06) !important;
    }

    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #E8E8F0;
        letter-spacing: -0.01em;
    }
    .sidebar-subtitle {
        font-size: 0.8rem;
        color: #6B6B90;
        margin-top: 2px;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #9090A8 !important;
        font-size: 0.85rem !important;
    }

    /* Sidebar button */
    [data-testid="stSidebar"] .stButton > button {
        background-color: rgba(139, 92, 246, 0.08) !important;
        color: #B8A0F0 !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        padding: 0.5rem 1rem !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(139, 92, 246, 0.18) !important;
        border-color: rgba(139, 92, 246, 0.35) !important;
        color: #D4C4F8 !important;
    }

    /* Sidebar slider track */
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #8B5CF6 !important;
    }

    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(139, 92, 246, 0.08) !important;
        margin: 1rem 0 !important;
    }

    /* ── Chat Messages (custom HTML) ──────────────────────────────────── */
    .chat-container {
        max-width: 780px;
        margin: 0 auto;
        padding: 0 1rem 6rem 1rem;
    }

    .msg-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 1.5rem;
        animation: msg-fade 0.15s ease-out;
    }
    @keyframes msg-fade {
        from { opacity: 0; }
        to   { opacity: 1; }
    }

    /* User row — right aligned */
    .msg-row.user {
        flex-direction: row-reverse;
    }

    /* Avatar */
    .msg-avatar {
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        margin-top: 2px;
    }

    /* Bubble — Assistant */
    .msg-bubble.assistant {
        color: #D4D4E4;
        font-size: 0.92rem;
        line-height: 1.75;
        padding: 4px 0;
        max-width: 85%;
    }
    .msg-bubble.assistant strong { color: #E8E8F0; }
    .msg-bubble.assistant code {
        background: rgba(139, 92, 246, 0.1);
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.84rem;
        color: #C4B5FD;
    }

    /* Bubble — User */
    .msg-bubble.user {
        background: linear-gradient(135deg, #2A2650 0%, #252248 100%);
        border: 1px solid rgba(139, 92, 246, 0.1);
        border-radius: 20px 20px 20px 20px;
        padding: 12px 18px;
        color: #E0E0F0;
        font-size: 0.92rem;
        line-height: 1.6;
        max-width: 75%;
    }

    /* ── Hide default st.chat_message styling ─────────────────────────── */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }

    /* ── Chat Input ───────────────────────────────────────────────────── */
    [data-testid="stChatInput"] {
        max-width: 780px !important;
        margin: 0 auto !important;
    }
    [data-testid="stChatInput"] > div {
        background-color: #1C1C36 !important;
        border: 1px solid rgba(139, 92, 246, 0.16) !important;
        border-radius: 24px !important;
        padding: 4px 6px !important;
        transition: border-color 0.2s ease !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: rgba(139, 92, 246, 0.45) !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #E0E0F0 !important;
        caret-color: #8B5CF6 !important;
        font-size: 0.94rem !important;
        line-height: 1.5 !important;
        padding: 8px 12px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #55557A !important;
    }
    /* Send button */
    [data-testid="stChatInput"] button {
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        border-radius: 50% !important;
        margin: 0 4px 4px 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stChatInput"] button[disabled] {
        background-color: transparent !important;
        background: transparent !important;
        color: #55557A !important;
        opacity: 0.4 !important;
    }
    [data-testid="stChatInput"] button[disabled] svg {
        fill: #55557A !important;
    }
    [data-testid="stChatInput"] button:not([disabled]) {
        background-color: #8B5CF6 !important;
        background: #8B5CF6 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    [data-testid="stChatInput"] button:not([disabled]) svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    [data-testid="stChatInput"] button:not([disabled]):hover {
        background-color: #9D74F7 !important;
        background: #9D74F7 !important;
    }

    /* ── Bottom bar background fix ────────────────────────────────────── */
    [data-testid="stBottom"] {
        background: linear-gradient(to top, #131320 85%, transparent) !important;
    }

    /* ── Landing Hero ─────────────────────────────────────────────────── */
    .amy-hero {
        text-align: center;
        padding: 8vh 2rem 0 2rem;
        max-width: 580px;
        margin: 0 auto 2.2rem auto;
    }
    .amy-hero-title {
        font-size: 2.8rem;
        font-weight: 600;
        background: linear-gradient(135deg, #8B5CF6 0%, #C4B5FD 50%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.03em;
        margin-bottom: 0.6rem;
    }
    .amy-hero-sub {
        color: #8888A4;
        font-size: 0.96rem;
        font-weight: 400;
        line-height: 1.65;
    }

    /* ── Main Area Suggestion Chips (Minimal & Clean) ─────────────────── */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        justify-content: center !important;
        align-items: center !important;
        gap: 10px !important;
        max-width: 780px !important;
        margin: 0 auto !important;
        flex-wrap: wrap !important;
    }
    [data-testid="stMain"] div[data-testid="column"] {
        flex: 0 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stMain"] div[data-testid="stButton"] > button,
    [data-testid="stMain"] button[data-testid="baseButton-secondary"],
    [data-testid="stMainBlockContainer"] .stButton > button,
    div[data-testid="column"] .stButton > button {
        background-color: #131320 !important;
        background: #131320 !important;
        color: #8C8CA8 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 9999px !important;
        padding: 10px 20px !important;
        font-size: 0.84rem !important;
        font-weight: 400 !important;
        text-align: center !important;
        line-height: 1.3 !important;
        white-space: nowrap !important;
        height: auto !important;
        width: auto !important;
        min-width: 0 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
        cursor: pointer !important;
    }
    [data-testid="stMain"] div[data-testid="stButton"] > button:hover,
    [data-testid="stMain"] button[data-testid="baseButton-secondary"]:hover,
    [data-testid="stMainBlockContainer"] .stButton > button:hover,
    div[data-testid="column"] .stButton > button:hover {
        background-color: #1A1A30 !important;
        background: #1A1A30 !important;
        border-color: rgba(139, 92, 246, 0.35) !important;
        color: #DDD6FE !important;
        box-shadow: none !important;
        transform: none !important;
    }
    [data-testid="stMain"] div[data-testid="stButton"] > button:active,
    [data-testid="stMain"] div[data-testid="stButton"] > button:focus {
        background-color: #1E1E38 !important;
        border-color: rgba(139, 92, 246, 0.5) !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* ── Source Chips ──────────────────────────────────────────────────── */
    .source-chip {
        display: inline-block;
        background-color: rgba(139, 92, 246, 0.06);
        color: #A78BFA;
        border: 1px solid rgba(139, 92, 246, 0.12);
        border-radius: 8px;
        padding: 3px 10px;
        font-size: 0.73rem;
        font-family: 'Inter', monospace;
        margin-right: 6px;
        margin-top: 10px;
        letter-spacing: 0.01em;
        text-decoration: none;
    }
    a.source-chip:hover {
        background-color: rgba(139, 92, 246, 0.15);
    }

    /* ── Typing Indicator ─────────────────────────────────────────────── */
    .typing-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 1.5rem;
    }
    .typing-dots {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 14px 0 14px 0;
    }
    .typing-dot {
        width: 7px;
        height: 7px;
        background-color: #8B5CF6;
        border-radius: 50%;
        animation: dot-pulse 1.4s infinite ease-in-out;
        opacity: 0.3;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dot-pulse {
        0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); }
        40% { opacity: 1; transform: scale(1.1); }
    }

    /* ── Scrollbar ────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.15);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.3);
    }

    /* ── Responsive ───────────────────────────────────────────────────── */
    @media (max-width: 768px) {
        .amy-hero { padding: 6vh 1rem 1rem 1rem; }
        .amy-hero-title { font-size: 2rem; }
        .msg-bubble.user { max-width: 88%; }
        .chat-container { padding: 0 0.5rem 6rem 0.5rem; }
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper — render a single chat message as HTML
# ---------------------------------------------------------------------------
def render_message(role: str, content: str) -> str:
    """Return HTML for a single chat message row."""
    if role == "user":
        avatar = AVATAR_USER
        bubble_cls = "user"
        row_cls = "user"
    else:
        avatar = AVATAR_AMY
        bubble_cls = "assistant"
        row_cls = "assistant"

    return (
        f'<div class="msg-row {row_cls}">'
        f'  <div class="msg-avatar">{avatar}</div>'
        f'  <div class="msg-bubble {bubble_cls}">{content}</div>'
        f'</div>'
    )


def render_typing_indicator() -> str:
    """Return HTML for the animated typing indicator."""
    return (
        f'<div class="typing-row">'
        f'  <div class="msg-avatar">{AVATAR_AMY}</div>'
        f'  <div class="typing-dots">'
        f'    <div class="typing-dot"></div>'
        f'    <div class="typing-dot"></div>'
        f'    <div class="typing-dot"></div>'
        f'  </div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">✦ Amy</div>'
        '<div class="sidebar-subtitle">Assistant Coach · Amnesia Esports</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    top_k = st.slider(
        "Context Depth",
        min_value=1,
        max_value=10,
        value=5,
        help="Number of document chunks to retrieve for each query.",
    )

    enable_google_search = st.toggle(
        "Enable Google Search",
        value=True,
        help="Allow Amy to use Google Search Grounding for live web facts if needed.",
    )

    st.divider()

    if st.button("New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ---------------------------------------------------------------------------
# Initialize chat history
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------------------------------
# Landing State (no messages)
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="amy-hero">
            <div class="amy-hero-title">Hi, I'm Amy</div>
            <div class="amy-hero-sub">
                Your AI Assistant Coach for Amnesia Esports.<br>
                Ask me about tournament rules, patch notes, and team strategy.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggestion chips — centered pill layout
    cols = st.columns(len(SUGGESTION_CHIPS))
    for i, chip in enumerate(SUGGESTION_CHIPS):
        with cols[i]:
            if st.button(chip["label"], key=f"chip_{i}"):
                st.session_state["_pending_query"] = chip["query"]
                st.rerun()


# ---------------------------------------------------------------------------
# Chat History & Dynamic UI
# ---------------------------------------------------------------------------
chat_placeholder = st.empty()


def update_chat_display(show_typing: bool = False) -> None:
    """Render the full chat conversation in the unified placeholder."""
    if not st.session_state.messages and not show_typing:
        chat_placeholder.empty()
        return

    html = '<div class="chat-container">'
    for msg in st.session_state.messages:
        html += render_message(msg["role"], msg["content"])
    if show_typing:
        html += render_typing_indicator()
    html += "</div>"
    chat_placeholder.markdown(html, unsafe_allow_html=True)


# Render existing messages
update_chat_display(show_typing=False)

# ---------------------------------------------------------------------------
# Process Query (from typed input OR suggestion chip)
# ---------------------------------------------------------------------------
pending = st.session_state.pop("_pending_query", None)
user_input = st.chat_input("Ask Amy anything...")
prompt = user_input or pending

if prompt:
    # 1. Append user message once
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Show conversation with typing indicator
    update_chat_display(show_typing=True)

    # 3. Fetch response from FastAPI backend
    try:
        payload = {
            "question": prompt,
            "top_k": top_k,
            "enable_google_search": enable_google_search
        }
        response = requests.post(QUERY_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        answer = data.get("answer", "I couldn't generate an answer.")
        sources = data.get("sources", [])

        full_response = answer
        if sources:
            full_response += '<div style="margin-top: 10px;">'
            doc_files = set()
            web_links = set()
            
            for s in sources:
                stype = s.get("source_type")
                if stype == "document":
                    fname = s.get("file_name", "Unknown")
                    if fname not in doc_files:
                        doc_files.add(fname)
                        full_response += f'<span class="source-chip">📄 {fname}</span>'
                elif stype == "web":
                    title = s.get("title", "Web Source")
                    url = s.get("url", "#")
                    if url not in web_links:
                        web_links.add(url)
                        full_response += f'<a href="{url}" target="_blank" class="source-chip">🌐 {title}</a>'
                        
            full_response += "</div>"

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

    except requests.exceptions.ConnectionError:
        error_content = (
            "<strong>Connection Error</strong> — "
            "The API server is not reachable. "
            "Make sure the FastAPI backend is running on port 8080."
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": error_content}
        )

    except requests.exceptions.HTTPError as e:
        error_content = f"<strong>API Error</strong> — {e.response.text}"
        st.session_state.messages.append(
            {"role": "assistant", "content": error_content}
        )

    # 4. Refresh display with the assistant's answer (typing indicator removed)
    update_chat_display(show_typing=False)
