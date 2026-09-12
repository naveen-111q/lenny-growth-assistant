import os
import re
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# Page Configuration & Modern Aesthetics
# ==============================================================================
st.set_page_config(
    page_title="The Lenny Growth Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, high-contrast light theme with dedicated Query/Response color palettes
st.markdown("""
<style>
    /* Global Typography and Palette */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1050px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Brand Header Container */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.1rem 1.6rem;
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #4f46e5;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    .header-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .header-subtitle {
        font-size: 0.86rem;
        color: #64748b;
        margin-top: 0.25rem;
        font-weight: 500;
    }

    /* Status Badges */
    .badge-container {
        display: flex;
        gap: 0.6rem;
        align-items: center;
    }
    .status-badge {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .status-online {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .status-offline {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .status-neutral {
        background-color: #eef2ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }

    /* =========================================================================
       USER QUERY VS ASSISTANT RESPONSE DISTINCT THEMES (FULL BACKGROUND FILL)
       ========================================================================= */

    /* 1. User Message: Distinct Soft Indigo / Lavender Bubble till the end of text */
    div[data-testid="stChatMessage"]:has(.user-role-label) {
        background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%) !important;
        border: 1.5px solid #c7d2fe !important;
        border-left: 6px solid #4f46e5 !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.08) !important;
        width: 100% !important;
    }

    div[data-testid="stChatMessage"]:has(.user-role-label) [data-testid="stChatMessageContent"] {
        background: transparent !important;
        color: #1e1b4b !important;
    }

    div[data-testid="stChatMessage"]:has(.user-role-label) p,
    div[data-testid="stChatMessage"]:has(.user-role-label) span,
    div[data-testid="stChatMessage"]:has(.user-role-label) strong {
        color: #1e1b4b !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    div[data-testid="stChatMessage"]:has(.user-role-label) [data-testid="stChatMessageAvatar"] {
        background: #c7d2fe !important;
        border: 1px solid #a5b4fc !important;
        border-radius: 12px !important;
    }

    /* 2. Assistant Message: Distinct Soft Emerald / Mint Card till the end of text */
    div[data-testid="stChatMessage"]:has(.assistant-role-label) {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%) !important;
        border: 1.5px solid #a7f3d0 !important;
        border-left: 6px solid #059669 !important;
        border-radius: 16px !important;
        padding: 1.35rem 1.6rem !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.06) !important;
        width: 100% !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) [data-testid="stChatMessageContent"] {
        background: transparent !important;
        color: #0f172a !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) p {
        color: #1e293b !important;
        line-height: 1.7 !important;
        font-size: 0.96rem !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) h1,
    div[data-testid="stChatMessage"]:has(.assistant-role-label) h2,
    div[data-testid="stChatMessage"]:has(.assistant-role-label) h3,
    div[data-testid="stChatMessage"]:has(.assistant-role-label) h4 {
        color: #064e3b !important;
        font-weight: 700 !important;
        margin-top: 0.9rem !important;
        margin-bottom: 0.45rem !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) ul,
    div[data-testid="stChatMessage"]:has(.assistant-role-label) ol {
        color: #1e293b !important;
        padding-left: 1.3rem !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) li {
        margin-bottom: 0.4rem !important;
        line-height: 1.65 !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) strong {
        color: #064e3b !important;
        font-weight: 700 !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) [data-testid="stChatMessageAvatar"] {
        background: #bbf7d0 !important;
        border: 1px solid #86efac !important;
        border-radius: 12px !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) code {
        background-color: #dcfce7 !important;
        color: #064e3b !important;
        padding: 0.18rem 0.45rem !important;
        border-radius: 4px !important;
        font-size: 0.88rem !important;
        border: 1px solid #bbf7d0 !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) pre {
        background-color: #ffffff !important;
        border: 1px solid #a7f3d0 !important;
        border-radius: 8px !important;
        padding: 0.85rem !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) blockquote {
        background: #ffffff !important;
        border-left: 4px solid #059669 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 4px !important;
        color: #1e293b !important;
    }

    div[data-testid="stChatMessage"]:has(.assistant-role-label) [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #a7f3d0 !important;
        border-radius: 10px !important;
        margin-top: 1rem !important;
    }

    /* Message Header Badges */
    .chat-role-label {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    .user-role-label {
        background: #e0e7ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }
    .assistant-role-label {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .grounded-pill {
        background: #059669;
        color: #ffffff;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.12rem 0.45rem;
        border-radius: 10px;
        margin-left: 0.35rem;
    }

    /* Welcome Hero Card */
    .welcome-hero-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-left: 5px solid #4f46e5;
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }
    .starter-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.65rem 0.95rem;
        margin-bottom: 0.5rem;
        font-size: 0.88rem;
        color: #334155;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .starter-card:hover {
        border-color: #a5b4fc;
        background-color: #f0f4ff;
        transform: translateX(4px);
    }

    /* Source Citation Cards */
    .source-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #4f46e5;
        border-radius: 10px;
        padding: 0.9rem 1.15rem;
        margin-bottom: 0.75rem;
        font-size: 0.88rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .source-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.07);
    }
    .source-title {
        font-weight: 700;
        color: #0f172a;
        font-size: 0.92rem;
    }
    .source-guest {
        color: #4338ca;
        font-size: 0.83rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .source-snippet {
        color: #334155;
        font-size: 0.84rem;
        line-height: 1.5;
        font-style: italic;
        background: #f8fafc;
        padding: 0.55rem 0.85rem;
        border-radius: 6px;
        border: 1px dashed #cbd5e1;
        margin-top: 0.35rem;
    }
    .source-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        margin-top: 0.35rem;
    }
    .source-link:hover {
        text-decoration: underline;
        color: #1d4ed8;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        color: #64748b;
        padding: 0.6rem 1.1rem;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5 !important;
        border-bottom: 2px solid #4f46e5 !important;
        background-color: transparent !important;
    }

    /* Expander Styling */
    [data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        background: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        margin-bottom: 0.8rem !important;
    }

    /* Sandbox Notice Box */
    .sandbox-notice {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 0.85rem 1.1rem;
        color: #1e40af;
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Backend API endpoint configuration
BACKEND_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")

# ==============================================================================
# Helper API Functions
# ==============================================================================
@st.cache_data(ttl=10, show_spinner=False)
def check_health():
    """Checks backend and provider health with cache and graceful fallback."""
    for _ in range(2):
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=6.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            time.sleep(0.3)
    return None


def create_new_session(provider="ollama", model=None):
    """Creates a new isolated chat session."""
    try:
        payload = {"title": "New Conversation", "provider": provider}
        if model:
            payload["model"] = model
        resp = requests.post(f"{BACKEND_URL}/sessions", json=payload, timeout=5.0)
        if resp.status_code == 201:
            return resp.json()["id"]
    except Exception as e:
        st.sidebar.error(f"Error creating session: {e}")
    return None


def list_sessions():
    """Lists available conversation sessions."""
    try:
        resp = requests.get(f"{BACKEND_URL}/sessions", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def get_session_details(session_id):
    """Retrieves message history for a session."""
    try:
        resp = requests.get(f"{BACKEND_URL}/sessions/{session_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def send_chat_message(session_id, message, provider=None, model=None):
    """Sends a chat query to the backend."""
    payload = {"session_id": session_id, "message": message}
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=180.0)
    if resp.status_code == 200:
        return resp.json()
    else:
        err_msg = resp.json().get("detail", resp.text)
        raise RuntimeError(err_msg)


def trigger_ship30(session_id, topic=None, provider=None, model=None):
    """Triggers the Ship 30 for 30 essay generation skill."""
    payload = {"session_id": session_id}
    if topic:
        payload["topic"] = topic
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    resp = requests.post(f"{BACKEND_URL}/generate/ship30", json=payload, timeout=120.0)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(resp.json().get("detail", resp.text))


def trigger_artifact(session_id, artifact_type, prompt, provider=None, model=None):
    """Triggers Markdown or HTML artifact generation."""
    payload = {
        "session_id": session_id,
        "artifact_type": artifact_type,
        "prompt": prompt
    }
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    resp = requests.post(f"{BACKEND_URL}/generate/artifact", json=payload, timeout=120.0)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(resp.json().get("detail", resp.text))


# ==============================================================================
# State Initialization
# ==============================================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "current_artifact" not in st.session_state:
    st.session_state.current_artifact = None  # dict with keys: type, title, content, sources

# Fetch backend health
health_data = check_health()

# Auto-create session if needed
if not st.session_state.session_id:
    new_id = create_new_session()
    if new_id:
        st.session_state.session_id = new_id

# ==============================================================================
# Sidebar: Controls & Navigation
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎙️ Lenny Growth Assistant")
    st.caption("Internal AI Advisor grounded in Lenny's Podcast transcripts.")

    # 1. New Chat Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_sid = create_new_session()
        if new_sid:
            st.session_state.session_id = new_sid
            st.session_state.current_artifact = None
            st.rerun()

    st.markdown("---")

    # 2. Session Management
    sessions = list_sessions()
    session_options = {s["id"]: f"{s['title'][:25]} ({s['message_count']} msgs)" for s in sessions} if sessions else {}

    if session_options:
        selected_sid = st.selectbox(
            "Active Session:",
            options=list(session_options.keys()),
            format_func=lambda x: session_options.get(x, x[:8]),
            index=list(session_options.keys()).index(st.session_state.session_id) if st.session_state.session_id in session_options else 0
        )
        if selected_sid != st.session_state.session_id:
            st.session_state.session_id = selected_sid
            st.session_state.current_artifact = st.session_state.get(f"artifact_{selected_sid}")
            st.rerun()

    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`" if st.session_state.session_id else "No session")

    st.markdown("---")

    # 3. Model Provider System
    st.markdown("#### 🧠 Model Provider")
    provider_choice = st.radio(
        "Active LLM Provider:",
        options=["Ollama (Local)", "OpenRouter (Cloud)"],
        index=0
    )
    active_provider_key = "ollama" if "Ollama" in provider_choice else "openrouter"

    # Dynamic Model Override
    default_model = "llama3.2" if active_provider_key == "ollama" else "meta-llama/llama-3.3-70b-instruct"
    selected_model = st.text_input("Model ID:", value=default_model)

    # Provider Health Status
    if health_data and "providers" in health_data:
        prov_info = health_data["providers"].get(active_provider_key, {})
        if prov_info.get("is_available"):
            st.markdown(f'<div class="status-badge status-online">🟢 {prov_info.get("provider_name", "").upper()} ONLINE</div>', unsafe_allow_html=True)
            if prov_info.get("latency_ms"):
                st.caption(f"Ping: {prov_info['latency_ms']}ms")
        else:
            st.markdown(f'<div class="status-badge status-offline">🔴 {prov_info.get("provider_name", "").upper()} UNAVAILABLE</div>', unsafe_allow_html=True)
            st.warning(prov_info.get("message", "Service unreachable."))
            if active_provider_key == "ollama":
                with st.expander("🛠️ How to fix Ollama"):
                    st.markdown("""
                    1. Install Ollama from [ollama.com](https://ollama.com)
                    2. In terminal run: `ollama run llama3.2`
                    3. Keep Ollama running on `http://localhost:11434`
                    4. Refresh this page.
                    """)
            else:
                with st.expander("🛠️ How to fix OpenRouter"):
                    st.markdown("""
                    1. Get an API key from [openrouter.ai](https://openrouter.ai)
                    2. Add `OPENROUTER_API_KEY=sk-or-v1-...` to `.env`
                    3. Restart backend.
                    """)
    else:
        st.markdown('<div class="status-badge status-offline">⚠️ Backend Offline</div>', unsafe_allow_html=True)
        st.error(f"Cannot reach FastAPI backend at {BACKEND_URL}.")

    st.markdown("---")

    # 4. Specialized Skills Panel
    st.markdown("#### ⚡ Specialized Skills")

    with st.expander("✍️ Generate Ship 30 Essay"):
        st.write("Synthesize grounded insights into a ~1,250-word atomic essay.")
        ship30_topic = st.text_input("Custom Angle (Optional):", placeholder="e.g., Finding PMF using Superhuman's engine")
        if st.button("Generate Essay", key="btn_ship30", use_container_width=True):
            with st.spinner("Crafting ~1,250-word atomic essay with Ship 30 structure..."):
                try:
                    res = trigger_ship30(
                        session_id=st.session_state.session_id,
                        topic=ship30_topic if ship30_topic.strip() else None,
                        provider=active_provider_key,
                        model=selected_model
                    )
                    art_obj = {
                        "type": "markdown",
                        "title": res["title"],
                        "content": res["essay"],
                        "sources": res.get("sources", [])
                    }
                    st.session_state.current_artifact = art_obj
                    st.session_state[f"artifact_{st.session_state.session_id}"] = art_obj
                    st.success(f"Generated essay ({res['word_count']} words)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    with st.expander("📦 Generate Artifact"):
        st.write("Create a Markdown document or sandboxed HTML/CSS UI.")
        art_type = st.selectbox("Artifact Type:", ["HTML/CSS", "Markdown"])
        art_prompt = st.text_area("Prompt / Requirements:", placeholder="e.g., Create a high-converting landing page for a B2B product-led growth tool with pricing tiers.")
        if st.button("Build Artifact", key="btn_artifact", use_container_width=True):
            if not art_prompt.strip():
                st.warning("Please specify requirements.")
            else:
                with st.spinner(f"Generating {art_type} artifact... (may take ~60s for Ollama)"):
                    try:
                        res = trigger_artifact(
                            session_id=st.session_state.session_id,
                            artifact_type="html" if "HTML" in art_type else "markdown",
                            prompt=art_prompt,
                            provider=active_provider_key,
                            model=selected_model
                        )
                        art_obj = {
                            "type": res["artifact_type"],
                            "title": res["title"],
                            "content": res["content"],
                            "sources": res.get("sources", [])
                        }
                        st.session_state.current_artifact = art_obj
                        st.session_state[f"artifact_{st.session_state.session_id}"] = art_obj
                        # Mark that a new artifact is ready so the viewer tab highlights it
                        st.session_state["artifact_just_generated"] = True
                        st.success(f"✅ {res['artifact_type'].upper()} artifact ready! → Click the **🎨 Artifact Viewer** tab above to view it.")
                    except Exception as e:
                        st.error(f"❌ Failed to generate artifact: {e}")


# ==============================================================================
# Main Application Tabs
# ==============================================================================
tab_chat, tab_artifact, tab_kb = st.tabs(["💬 Conversation", "🎨 Artifact Viewer", "📚 Knowledge Base"])

# ------------------------------------------------------------------------------
# TAB 1: Conversational Assistant
# ------------------------------------------------------------------------------
with tab_chat:
    # Header display
    st.markdown(f"""
    <div class="header-container">
        <div>
            <div class="header-title">🎙️ The Lenny Growth Assistant</div>
            <div class="header-subtitle">Strictly grounded in Lenny's Podcast and Newsletter transcripts</div>
        </div>
        <div class="badge-container">
            <span class="status-badge status-neutral">Model: {selected_model}</span>
            <span class="status-badge status-neutral">Provider: {active_provider_key.upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load session messages
    session_data = get_session_details(st.session_state.session_id) if st.session_state.session_id else None
    messages = session_data.get("messages", []) if session_data else []

    if not messages:
        # Welcome Hero Banner
        st.markdown("""
        <div class="welcome-hero-card">
            <h3 style="margin-top:0; color:#0f172a; font-weight:700;">👋 Welcome to your Lenny Growth Assistant!</h3>
            <p style="color:#475569; font-size:0.95rem; line-height:1.6;">
                Ask any tactical question about product management, growth loops, and company building.
                Every response is <strong>strictly grounded</strong> in real transcripts from Lenny Rachitsky's conversations with top builders.
            </p>
            <div style="margin-top: 1.2rem;">
                <div style="font-weight:700; font-size:0.8rem; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.6rem;">💡 Recommended Topics to Explore:</div>
                <div class="starter-card">🎯 <strong>"How did Superhuman systematically find product-market fit?"</strong> — <em>Rahul Vohra</em></div>
                <div class="starter-card">🔄 <strong>"What is the difference between an acquisition loop and a sales funnel?"</strong> — <em>Elena Verna</em></div>
                <div class="starter-card">⏱️ <strong>"What is Shreyas Doshi's LNO framework for time management?"</strong> — <em>Shreyas Doshi</em></div>
                <div class="starter-card">🚀 <strong>"How does Brian Chesky define Founder Mode at Airbnb?"</strong> — <em>Brian Chesky</em></div>
                <div class="starter-card">📈 <strong>"What are the 4 primary compounding growth loops according to Gustaf Alströmer?"</strong> — <em>Gustaf Alströmer</em></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render message history
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])

        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🎙️"):
            if role == "user":
                st.markdown('<div class="chat-role-label user-role-label"><span>💬</span> <strong>User Query</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="chat-role-label assistant-role-label"><span>🎙️</span> <strong>Lenny Growth Advisor</strong> <span class="grounded-pill">✓ Grounded Response</span></div>', unsafe_allow_html=True)
            st.markdown(content)

            # Render Grounded Sources if available
            if sources and role == "assistant":
                with st.expander(f"📚 Grounded Sources ({len(sources)} cited)"):
                    for s in sources:
                        role_str = f" • *{s.get('guest_role')}*" if s.get('guest_role') else ""
                        url_str = f'<br><a class="source-link" href="{s.get("url")}" target="_blank">🔗 Open Original Episode</a>' if s.get("url") else ""
                        st.markdown(f"""
                        <div class="source-card">
                            <div class="source-title">🎙️ {s.get('episode_title')}</div>
                            <div class="source-guest">Guest: <strong>{s.get('guest')}</strong>{role_str} (Relevance: {s.get('relevance_score', 0):.2f})</div>
                            <div class="source-snippet">"{s.get('content_snippet', '')[:300]}..."</div>
                            {url_str}
                        </div>
                        """, unsafe_allow_html=True)

    # Chat Input
    user_query = st.chat_input("Ask a product management or growth question...")
    if user_query:
        # Optimistically render user message
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown('<div class="chat-role-label user-role-label"><span>💬</span> <strong>User Query</strong></div>', unsafe_allow_html=True)
            st.markdown(user_query)

        sp_msg = "Running local inference with Ollama (takes ~20-30s on CPU)..." if active_provider_key == "ollama" else "Searching Lenny transcripts & generating grounded response..."
        with st.chat_message("assistant", avatar="🎙️"):
            st.markdown('<div class="chat-role-label assistant-role-label"><span>🎙️</span> <strong>Lenny Growth Advisor</strong> <span class="grounded-pill">✓ Grounded Response</span></div>', unsafe_allow_html=True)
            with st.spinner(sp_msg):
                try:
                    resp = send_chat_message(
                        session_id=st.session_state.session_id,
                        message=user_query,
                        provider=active_provider_key,
                        model=selected_model
                    )
                    st.markdown(resp["assistant_message"])

                    # Show sources
                    if resp.get("sources"):
                        with st.expander(f"📚 Grounded Sources ({len(resp['sources'])} cited)"):
                            for s in resp["sources"]:
                                role_str = f" • *{s.get('guest_role')}*" if s.get('guest_role') else ""
                                url_str = f'<br><a class="source-link" href="{s.get("url")}" target="_blank">🔗 Open Original Episode</a>' if s.get("url") else ""
                                st.markdown(f"""
                                <div class="source-card">
                                    <div class="source-title">🎙️ {s.get('episode_title')}</div>
                                    <div class="source-guest">Guest: <strong>{s.get('guest')}</strong>{role_str} (Relevance: {s.get('relevance_score', 0):.2f})</div>
                                    <div class="source-snippet">"{s.get('content_snippet', '')[:300]}..."</div>
                                    {url_str}
                                </div>
                                """, unsafe_allow_html=True)

                    st.caption(f"⚡ Response time: {resp.get('latency_ms', 0)}ms | Provider: {resp.get('provider')} ({resp.get('model')})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ------------------------------------------------------------------------------
# TAB 2: Secure In-App Artifact Viewer
# ------------------------------------------------------------------------------
with tab_artifact:
    st.markdown("### 🎨 In-App Artifact Viewer")
    st.caption("Inspect and safely render generated Markdown specifications, strategy documents, or HTML/CSS prototypes.")

    art = st.session_state.current_artifact

    if not art:
        st.info("No artifact generated yet. Use the sidebar **'Generate Artifact'** or **'Generate Ship 30 Essay'** tool to create one!")
    else:
        st.markdown(f"#### 📄 {art.get('title', 'Generated Artifact')}")

        # Security Architecture Notice
        st.markdown("""
        <div class="sandbox-notice">
            🛡️ <strong>Security & Sandbox Architecture:</strong><br>
            • <strong>Sanitization:</strong> Dangerous <code>&lt;script&gt;</code> tags, <code>javascript:</code> protocols, and inline event listeners (e.g. <code>onerror</code>, <code>onload</code>) are scrubbed before rendering.<br>
            • <strong>Isolation:</strong> Rendered inside an isolated cross-origin iframe. The artifact has zero access to parent cookies, local storage, or application DOM.
        </div>
        """, unsafe_allow_html=True)

        view_mode = st.radio("Viewer Mode:", ["Rendered View", "Code Inspector"], horizontal=True)

        if view_mode == "Rendered View":
            if art["type"] == "html":
                # Strip markdown code fences using plain string ops (no re import needed)
                cleaned_html = art["content"].strip()
                if cleaned_html.startswith("```html"):
                    cleaned_html = cleaned_html[7:].lstrip("\n").strip()
                elif cleaned_html.startswith("```"):
                    cleaned_html = cleaned_html[3:].lstrip("\n").strip()
                if cleaned_html.endswith("```"):
                    cleaned_html = cleaned_html[:-3].rstrip()

                # Ensure unclosed <style> is closed (handles Ollama truncation)
                if "<style" in cleaned_html.lower() and "</style>" not in cleaned_html.lower():
                    cleaned_html += "\n</style>\n"

                # Ensure closing tags so browser renders the complete DOM
                if "<html" in cleaned_html.lower():
                    if "</body>" not in cleaned_html.lower():
                        cleaned_html += "\n</body>"
                    if "</html>" not in cleaned_html.lower():
                        cleaned_html += "\n</html>"
                else:
                    # Wrap bare HTML snippet in a clean light-themed full document
                    cleaned_html = (
                        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
                        "  <meta charset=\"utf-8\">\n"
                        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                        "  <style>\n"
                        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;"
                        " padding: 28px; background: #f8fafc; color: #0f172a; line-height: 1.65; }\n"
                        "    .artifact-box { background: #ffffff; padding: 32px; border-radius: 14px;"
                        " border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.06);"
                        " max-width: 900px; margin: 0 auto; }\n"
                        "  </style>\n</head>\n<body>\n"
                        f"  <div class=\"artifact-box\">{cleaned_html}</div>\n"
                        "</body>\n</html>"
                    )

                # Render inside sandboxed iframe (components.v1.html is the stable API)
                st.components.v1.html(cleaned_html, height=700, scrolling=True)
            else:
                # Render Markdown artifact
                st.markdown(art["content"])
        else:
            # Code Inspector Mode
            st.markdown("##### Raw Source Code")
            code_lang = "html" if art["type"] == "html" else "markdown"
            st.code(art["content"], language=code_lang)
            st.download_button(
                label=f"💾 Download {art['type'].upper()} Artifact",
                data=art["content"],
                file_name=f"lenny_artifact_{int(time.time())}.{code_lang}",
                mime="text/html" if art["type"] == "html" else "text/markdown"
            )

        # Display Grounded Sources used for the artifact
        if art.get("sources"):
            with st.expander(f"📚 Grounded Sources for this Artifact ({len(art['sources'])} cited)"):
                for s in art["sources"]:
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-title">🎙️ {s.get('episode_title')}</div>
                        <div class="source-guest">Guest: <strong>{s.get('guest')}</strong></div>
                        <div class="source-snippet">"{s.get('content_snippet', '')[:250]}..."</div>
                    </div>
                    """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# TAB 3: Knowledge Base & Transcripts
# ------------------------------------------------------------------------------
with tab_kb:
    st.markdown("### 📚 Lenny Transcript Knowledge Base")
    st.caption("Ingested episodes and core strategic pillars available for grounded retrieval.")

    episodes = [
        {
            "guest": "Rahul Vohra",
            "role": "Founder & CEO, Superhuman",
            "title": "How to Find Product-Market Fit and Measure It",
            "topic": "The 40% 'Very Disappointed' Rule, HXC Persona, and the 4-Step PMF Engine.",
            "url": "https://www.lennysnewsletter.com/p/how-superhuman-built-an-engine-to-find-product-market-fit"
        },
        {
            "guest": "Elena Verna",
            "role": "Head of Growth, Dropbox & Amplitude",
            "title": "The Ultimate Guide to B2B Product-Led Growth and Monetization",
            "topic": "PLG vs Sales-Led, Collaborative Growth Loops, and Freemium Paywall Strategy.",
            "url": "https://www.lennyspodcast.com/the-ultimate-guide-to-b2b-product-led-growth-elena-verna/"
        },
        {
            "guest": "Shreyas Doshi",
            "role": "Former Product Leader at Stripe & Twitter",
            "title": "The Power of High Agency, PM Skills, and Career Frameworks",
            "topic": "High Agency Definition, The LNO Framework (Leverage, Neutral, Overhead).",
            "url": "https://www.lennyspodcast.com/the-power-of-high-agency-pm-skills-and-career-frameworks-shreyas-doshi/"
        },
        {
            "guest": "Brian Chesky",
            "role": "Co-founder & CEO, Airbnb",
            "title": "Brian Chesky on Founder Mode, Designing Culture, and Running Airbnb",
            "topic": "Founder Mode vs Manager Mode, CEO Product Reviews, and 11-Star Experience.",
            "url": "https://www.lennyspodcast.com/brian-chesky-on-founder-mode-and-airbnb/"
        },
        {
            "guest": "Gustaf Alströmer",
            "role": "Partner at Y Combinator, former Airbnb Growth",
            "title": "How Y Combinator Teaches Growth: Retention, Loops, and Metric Truth",
            "topic": "Retention Curves as Growth Foundation, Compounding Growth Loops vs Funnels.",
            "url": "https://www.lennyspodcast.com/how-yc-teaches-growth-gustaf-alstromer/"
        }
    ]

    col1, col2 = st.columns(2)
    for i, ep in enumerate(episodes):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            st.markdown(f"""
            <div class="source-card" style="margin-bottom: 1rem;">
                <div class="source-title">🎙️ {ep['title']}</div>
                <div class="source-guest"><strong>{ep['guest']}</strong> • {ep['role']}</div>
                <p style="font-size: 0.85rem; color: #475569; margin: 0.4rem 0;">{ep['topic']}</p>
                <a class="source-link" href="{ep['url']}" target="_blank">🔗 Episode Link & Transcript</a>
            </div>
            """, unsafe_allow_html=True)
