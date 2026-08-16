"""
Streamlit Frontend for Amy Team Chatbot.

Provides a modern, high-end AI chat interface for Amnesia Esports team members
to interact with the RAG Assistant Coach.
"""

import base64
import os
from urllib.parse import urljoin

import requests
import streamlit as st

# =============================================================================
# Configuration
# =============================================================================

API_HOST = os.getenv("API_HOST", "http://localhost:8080")
QUERY_ENDPOINT = urljoin(API_HOST, "/query")

# SVG Avatars for brand fidelity
SVG_AMY = """<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="36" height="36" rx="10" fill="url(#amy_grad)"/>
<path d="M18 9L20.2 15.8L27 18L20.2 20.2L18 27L15.8 20.2L9 18L15.8 15.8L18 9Z" fill="white"/>
<defs>
<linearGradient id="amy_grad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
<stop stop-color="#8B5CF6"/>
<stop offset="1" stop-color="#6366F1"/>
</linearGradient>
</defs>
</svg>"""

SVG_USER = """<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="36" height="36" rx="10" fill="#252440"/>
<circle cx="18" cy="14" r="5" stroke="#A78BFA" stroke-width="1.8" fill="none"/>
<path d="M10 27c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke="#A78BFA" stroke-width="1.8" fill="none" stroke-linecap="round"/>
</svg>"""


def get_svg_data_url(svg_str: str) -> str:
    b64 = base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


AVATAR_AMY = get_svg_data_url(SVG_AMY)
AVATAR_USER = get_svg_data_url(SVG_USER) + "#user"

# =============================================================================
# Page Setup
# =============================================================================

st.set_page_config(
    page_title="Amy — Assistant Coach",
    page_icon=":material/smart_toy:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# Design System & Styling (Dark Modern Cinematic Esports / AI Theme)
# =============================================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ---------- Global Core ---------- */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: #0E0E1A !important;
            color: #E6E8F5 !important;
        }

        /* Hide unwanted Streamlit UI elements */
        #MainMenu, [data-testid="stAppDeployButton"], footer, [data-testid="stToolbarActions"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Center main container */
        .block-container {
            max-width: 760px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 1.25rem !important;
            padding-bottom: 7rem !important;
        }

        /* ---------- Top Bar & Header ---------- */
        .brand-box {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .brand-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            box-shadow: 0 0 16px rgba(139, 92, 246, 0.4);
            color: #ffffff;
        }

        .brand-info {
            display: flex;
            flex-direction: column;
        }

        .brand-title {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #FFFFFF;
            line-height: 1.2;
        }

        .brand-badge {
            font-size: 0.72rem;
            font-weight: 500;
            color: #A78BFA;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        /* ---------- Popover (Settings) - Full Roundness ---------- */
        [data-testid="stPopover"] > button {
            border-radius: 9999px !important;
        }

        /* ---------- Hero / Landing State (Centered) ---------- */
        .hero-wrap {
            text-align: center;
            padding: 4rem 1rem 2rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }

        .hero-sparkle {
            width: 54px;
            height: 54px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(99, 102, 241, 0.15) 100%);
            border: 1px solid rgba(139, 92, 246, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #C4B5FD;
            box-shadow: 0 0 30px rgba(139, 92, 246, 0.25);
            margin-bottom: 1.25rem;
            animation: floatGlow 4s ease-in-out infinite alternate;
        }

        @keyframes floatGlow {
            0% { transform: translateY(0px); box-shadow: 0 0 20px rgba(139, 92, 246, 0.25); }
            100% { transform: translateY(-4px); box-shadow: 0 0 35px rgba(139, 92, 246, 0.45); }
        }

        .hero-heading {
            font-size: 2.3rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #A78BFA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 0.5rem 0;
            line-height: 1.2;
            text-align: center;
        }

        .hero-subheading {
            font-size: 0.98rem;
            color: #94A3B8;
            max-width: 520px;
            line-height: 1.6;
            margin-bottom: 2rem;
            text-align: center;
        }

        .suggestion-header {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #71717A;
            margin-bottom: 0.85rem;
            font-weight: 600;
            text-align: center;
        }

        /* ---------- Suggestion Pills / Buttons (Centered) ---------- */
        div.stElementContainer:has([data-testid="stPills"]),
        div[data-testid="stElementContainer"]:has([data-testid="stPills"]) {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }

        div[data-testid="stPills"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin: 0 auto 1.5rem auto !important;
        }

        div[data-testid="stPills"] div[role="radiogroup"],
        div[data-testid="stPills"] div[role="group"],
        div[data-testid="stPills"] > div,
        div[data-testid="stPills"] > div > div {
            display: flex !important;
            justify-content: center !important;
            flex-wrap: wrap !important;
            width: 100% !important;
            margin: 0 auto !important;
        }

        div[data-testid="stPills"] button {
            background-color: #16162C !important;
            border: 1px solid rgba(139, 92, 246, 0.2) !important;
            border-radius: 9999px !important;
            color: #E2E8F0 !important;
            font-size: 0.86rem !important;
            padding: 8px 18px !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        div[data-testid="stPills"] button:hover {
            border-color: rgba(139, 92, 246, 0.6) !important;
            background-color: #1F1F3D !important;
            color: #FFFFFF !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.2) !important;
        }

        /* ---------- Chat Messages ---------- */
        [data-testid="stChatMessage"] {
            padding: 0.75rem 0.25rem !important;
            background-color: transparent !important;
            gap: 1rem !important;
        }

        /* User Message Container & Bubble */
        [data-testid="stChatMessage"]:has(img[src*="#user"]) {
            flex-direction: row-reverse !important;
        }

        [data-testid="stChatMessage"]:has(img[src*="#user"]) [data-testid="stChatMessageContent"] {
            background: linear-gradient(135deg, #221F3D 0%, #1A1830 100%) !important;
            border: 1px solid rgba(139, 92, 246, 0.25) !important;
            border-radius: 18px 18px 4px 18px !important;
            padding: 12px 18px !important;
            color: #F1F1F8 !important;
            max-width: 82% !important;
            margin-left: auto !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
        }

        /* Assistant Message styling */
        [data-testid="stChatMessage"]:not(:has(img[src*="#user"])) [data-testid="stChatMessageContent"] {
            background: transparent !important;
            padding: 4px 0 !important;
            color: #E2E8F0 !important;
            line-height: 1.65 !important;
        }

        /* Code snippets */
        code {
            font-family: 'JetBrains Mono', monospace !important;
            background: #18182E !important;
            border: 1px solid rgba(139, 92, 246, 0.2) !important;
            border-radius: 6px !important;
            padding: 0.15rem 0.4rem !important;
            color: #C4B5FD !important;
            font-size: 0.88em !important;
        }

        /* ---------- Source Citations ---------- */
        .sources-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
            padding-top: 10px;
            border-top: 1px solid rgba(139, 92, 246, 0.15);
        }

        .source-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(139, 92, 246, 0.08);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 0.76rem;
            font-weight: 500;
            color: #C4B5FD;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        a.source-badge:hover {
            background: rgba(139, 92, 246, 0.2);
            border-color: rgba(139, 92, 246, 0.45);
            color: #FFFFFF;
            transform: translateY(-1px);
        }

        /* ---------- Bottom Bar & Chat Input Centering ---------- */
        [data-testid="stBottom"] {
            background-color: #0E0E1A !important;
        }

        [data-testid="stBottom"] > div {
            background-color: transparent !important;
            max-width: 760px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        [data-testid="stChatInput"] {
            max-width: 760px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        [data-testid="stChatInput"] > div {
            background-color: #151528 !important;
            border: 1px solid rgba(139, 92, 246, 0.25) !important;
            border-radius: 9999px !important;
            padding: 4px 10px !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4) !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }

        [data-testid="stChatInput"] > div:focus-within {
            border-color: rgba(139, 92, 246, 0.7) !important;
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.25) !important;
        }

        [data-testid="stChatInput"] button {
            border-radius: 50% !important;
            transition: transform 0.15s ease !important;
        }

        [data-testid="stChatInput"] button:not([disabled]) {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%) !important;
            color: #FFFFFF !important;
        }

        [data-testid="stChatInput"] button:not([disabled]):hover {
            transform: scale(1.06) !important;
        }

        /* ---------- Mobile Adjustments ---------- */
        @media (max-width: 768px) {
            .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
            .hero-heading { font-size: 1.85rem !important; }
            [data-testid="stChatMessage"]:has(img[src*="#user"]) [data-testid="stChatMessageContent"] { max-width: 90% !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# Session State Initialization
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "google_search" not in st.session_state:
    st.session_state.google_search = False

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 5


# =============================================================================
# Backend Communication
# =============================================================================

def ask_assistant(
    question: str,
    *,
    google_search: bool,
    chunk_count: int,
) -> str:
    """Send query to the FastAPI RAG backend and format the response with citations."""
    try:
        payload = {
            "question": question,
            "top_k": chunk_count,
            "enable_google_search": google_search,
        }
        response = requests.post(QUERY_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        answer = data.get("answer", "I couldn't generate an answer.")
        sources = data.get("sources", [])

        if sources:
            doc_files = set()
            web_links = set()
            chips = []

            for s in sources:
                stype = s.get("source_type")
                if stype == "document":
                    fname = s.get("file_name", "Unknown Document")
                    if fname not in doc_files:
                        doc_files.add(fname)
                        chips.append(
                            f'<span class="source-badge">'
                            f'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> '
                            f'{fname}</span>'
                        )
                elif stype == "web":
                    title = s.get("title", "Web Source")
                    url = s.get("url", "#")
                    if url not in web_links:
                        web_links.add(url)
                        chips.append(
                            f'<a href="{url}" target="_blank" class="source-badge">'
                            f'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> '
                            f'{title}</a>'
                        )

            if chips:
                answer += '\n\n<div class="sources-container">' + "".join(chips) + "</div>"

        return answer

    except requests.exceptions.ConnectionError:
        return (
            "**Connection Error**: Unable to reach the coaching server at `http://localhost:8080`.\n\n"
            "Please ensure the backend service is running with:\n"
            "```bash\npython -m src.main\n```"
        )
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 500
        if status_code == 429:
            return "**Rate Limit**: API quota limit reached. Please wait a moment or disable Google Search in settings."
        if status_code == 503:
            return "**Service Initializing**: The coaching engine is warming up. Please try again in a few seconds."
        return "**Unexpected Error**: The server encountered an issue processing your query. Please try rephrasing."
    except Exception as exc:
        return f"**Error**: {type(exc).__name__}: {exc}"


# =============================================================================
# Header & Navigation Bar (Centered Layout)
# =============================================================================

header_col_left, header_col_right = st.columns([3, 1], vertical_alignment="center")

with header_col_left:
    st.markdown(
        """
        <div class="brand-box">
            <div class="brand-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>
                </svg>
            </div>
            <div class="brand-info">
                <span class="brand-title">Amy</span>
                <span class="brand-badge">Amnesia Esports • AI Coach</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_col_right:
    with st.popover(":material/tune: Settings"):
        st.caption("ASSISTANT CAPABILITIES")
        st.session_state.google_search = st.toggle(
            "Google Search Grounding",
            value=st.session_state.google_search,
            help="Enable live web search for up-to-date tournament and patch updates.",
        )
        st.session_state.chunk_count = st.slider(
            "Knowledge Retrieval Depth",
            min_value=1,
            max_value=10,
            value=st.session_state.chunk_count,
            help="Number of document chunks retrieved per question.",
        )
        st.divider()
        if st.button(":material/delete: Clear Conversation", width="stretch"):
            st.session_state.messages = []
            st.rerun()


# =============================================================================
# Suggestion Prompts Definition (Material Icons, Zero Emojis)
# =============================================================================

SUGGESTIONS = {
    ":material/gavel: Disconnection rules": "What is the disconnection rule for Valorant tournaments?",
    ":material/description: Latest patch summary": "Summarize the key agent and weapon changes from the latest patch notes.",
    ":material/emoji_events: Tournament format": "Explain the tournament format, map veto process, and overtime rules.",
    ":material/psychology: Mental & match prep": "What strategic advice can you give for team communication under pressure?",
}


# =============================================================================
# Helper: Process and Stream Response
# =============================================================================

def process_query(user_text: str):
    """Adds the user query to state, renders the response immediately, and updates history."""
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar=AVATAR_USER):
        st.markdown(user_text)

    with st.chat_message("assistant", avatar=AVATAR_AMY):
        with st.spinner("Amy is analyzing team documents..."):
            answer = ask_assistant(
                user_text,
                google_search=st.session_state.google_search,
                chunk_count=st.session_state.chunk_count,
            )
            st.markdown(answer, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()


# =============================================================================
# Render Chat History
# =============================================================================

for msg in st.session_state.messages:
    avatar = AVATAR_USER if msg["role"] == "user" else AVATAR_AMY
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)


# =============================================================================
# Empty / Landing State (Hero + Action Pills)
# =============================================================================

if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-sparkle">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>
                </svg>
            </div>
            <h1 class="hero-heading">Hi, I'm Amy</h1>
            <div class="hero-subheading">
                Your AI Assistant Coach for <b>Amnesia Esports</b>.<br>
                Ask me about tournament rulebooks, tactical preparation, and patch updates.
            </div>
            <div class="suggestion-header">Suggested Prompts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_pill = st.pills(
        "Suggested Prompts",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
        key="hero_pills",
    )
    if selected_pill:
        prompt_text = SUGGESTIONS[selected_pill]
        process_query(prompt_text)


# =============================================================================
# Chat Input Bar (Native Bottom Docking & Centered)
# =============================================================================

if user_input := st.chat_input("Ask Amy about rules, strategy, or patches..."):
    cleaned_input = user_input.strip()
    if cleaned_input:
        process_query(cleaned_input)
