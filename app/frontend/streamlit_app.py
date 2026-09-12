import os
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

# Custom CSS for polished, ChatGPT-like interface
st.markdown("""
<style>
    /* Global Typography and Palette */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1050px;
    }

    /* Brand Header */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border-radius: 14px;
        border: 1px solid rgba(99, 102, 241, 0.25);
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .header-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 0.2rem;
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
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }
    .status-online {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-offline {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .status-neutral {
        background-color: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    /* Source Citation Cards */
    .source-card {
        background: #1e293b;
        border-left: 3px solid #6366f1;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        font-size: 0.88rem;
    }
    .source-title {
        font-weight: 600;
        color: #e2e8f0;
    }
    .source-guest {
        color: #a5b4fc;
        font-size: 0.82rem;
        margin-bottom: 0.4rem;
    }
    .source-snippet {
        color: #cbd5e1;
        font-size: 0.83rem;
        line-height: 1.4;
        font-style: italic;
    }
    .source-link {
        color: #38bdf8;
        text-decoration: none;
        font-size: 0.8rem;
        display: inline-block;
        margin-top: 0.3rem;
    }

    /* Sandbox Notice Box */
    .sandbox-notice {
        background: rgba(14, 165, 233, 0.1);
        border: 1px solid rgba(14, 165, 233, 0.3);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #38bdf8;
        font-size: 0.85rem;
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
    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=90.0)
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
                    st.session_state.current_artifact = {
                        "type": "markdown",
                        "title": res["title"],
                        "content": res["essay"],
                        "sources": res.get("sources", [])
                    }
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
                with st.spinner(f"Generating {art_type} artifact..."):
                    try:
                        res = trigger_artifact(
                            session_id=st.session_state.session_id,
                            artifact_type="html" if "HTML" in art_type else "markdown",
                            prompt=art_prompt,
                            provider=active_provider_key,
                            model=selected_model
                        )
                        st.session_state.current_artifact = {
                            "type": res["artifact_type"],
                            "title": res["title"],
                            "content": res["content"],
                            "sources": res.get("sources", [])
                        }
                        st.success(f"Generated {res['artifact_type'].upper()} artifact!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")


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
        ### Welcome to your Lenny Growth Assistant!
        Ask any tactical question about product management, growth, and company building. All answers are **strictly grounded** in the real transcripts of Lenny Rachitsky's conversations with top builders.

        **Try asking:**
        - *"How did Superhuman systematically find product-market fit?"*
        - *"What is the difference between an acquisition loop and a traditional sales funnel according to Elena Verna?"*
        - *"What is Shreyas Doshi's LNO framework for time management?"*
        - *"How does Brian Chesky define Founder Mode at Airbnb?"*
        - *"What are the 4 primary compounding growth loops according to Gustaf Alströmer?"*
        """)

    # Render message history
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])

        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🎙️"):
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
            st.markdown(user_query)

        # Send to backend
        with st.chat_message("assistant", avatar="🎙️"):
            with st.spinner("Searching Lenny transcripts & generating grounded response..."):
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
                # Render inside sandboxed iframe
                components.html(art["content"], height=650, scrolling=True)
            else:
                # Render Markdown
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
                <p style="font-size: 0.85rem; color: #cbd5e1; margin: 0.4rem 0;">{ep['topic']}</p>
                <a class="source-link" href="{ep['url']}" target="_blank">🔗 Episode Link & Transcript</a>
            </div>
            """, unsafe_allow_html=True)
