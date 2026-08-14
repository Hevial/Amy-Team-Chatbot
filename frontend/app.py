"""
Streamlit Frontend for Amy Team Chatbot.

Provides a chat interface for users to interact with the RAG Assistant Coach.
It connects to the FastAPI backend to retrieve answers and source citations.
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

st.set_page_config(
    page_title="Amy | Amnesia Esports",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for Esports Theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main Chat Area */
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Source Citations */
    .source-box {
        font-size: 0.8rem;
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 3px solid #FF4B4B;
        padding: 0.5rem 1rem;
        margin-top: 0.5rem;
        border-radius: 0 5px 5px 0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Esports_Logo.svg/1024px-Esports_Logo.svg.png", width=150)
    st.title("Amy Assistant")
    st.markdown("Your tactical and regulatory companion.")
    
    st.divider()
    
    st.markdown("### Settings")
    top_k = st.slider("Context Depth (Chunks)", min_value=1, max_value=10, value=5, help="Number of document chunks to retrieve.")
    
    st.divider()
    
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Main Chat Interface
# ---------------------------------------------------------------------------
st.title("🎮 Amy Team Chatbot")
st.caption("Ask me about tournament rules, agent patch notes, or team strategy.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm Amy, your Assistant Coach. How can I help you prepare for the Istanbul Invitational today?"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Chat Input & API Integration
# ---------------------------------------------------------------------------
if prompt := st.chat_input("E.g., What are the rules for tactical pauses?"):
    
    # 1. Add user message to state and UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call FastAPI backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Analyzing team documents..."):
                payload = {
                    "question": prompt,
                    "top_k": top_k
                }
                
                response = requests.post(QUERY_ENDPOINT, json=payload, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                answer = data.get("answer", "No answer provided.")
                sources = data.get("sources", [])
                
                # Format the response with citations
                full_response = answer + "\n\n"
                
                if sources:
                    full_response += "**Sources:**\n"
                    # Deduplicate source file names
                    source_files = list({s.get("file_name", "Unknown") for s in sources})
                    for sf in source_files:
                        full_response += f"- `{sf}`\n"
                
                # Render to UI
                message_placeholder.markdown(full_response)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except requests.exceptions.ConnectionError:
            error_msg = "🚨 **Connection Error:** Could not reach the API. Is the FastAPI server running on port 8080?"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"🚨 **API Error:** {e.response.text}"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
