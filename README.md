# 🎙️ The Lenny Growth Assistant

A production-grade, full-stack conversational AI assistant grounded strictly in **Lenny’s Podcast and Newsletter transcripts**. Built as a Forward Deployed Engineer take-home project with clean modular architecture, dual model provider abstraction (Ollama + OpenRouter), Ship 30 for 30 essay synthesis, and a sandboxed in-app Artifact Viewer.

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Architecture & Technology Stack](#-architecture--technology-stack)
3. [Prerequisites](#-prerequisites)
4. [Environment Configuration](#-environment-configuration)
5. [Ollama Setup (Mandatory for Demo)](#-ollama-setup-mandatory-for-demo)
6. [Running Locally (Without Docker)](#-running-locally-without-docker)
7. [Running with Docker Compose](#-running-with-docker-compose)
8. [Transcript Ingestion & RAG Knowledge Pipeline](#-transcript-ingestion--rag-knowledge-pipeline)
9. [Specialized Skills & Artifact Viewer](#-specialized-skills--artifact-viewer)
10. [Model Provider Switching](#-model-provider-switching)
11. [Automated Testing](#-automated-testing)
12. [Troubleshooting](#-troubleshooting)
13. [Discovery, Tradeoffs & Known Limitations](#-discovery-tradeoffs--known-limitations)

---

## 🎯 Project Overview

The **Lenny Growth Assistant** helps product managers, founders, and growth engineers tap into tactical wisdom from world-class operators interviewed by Lenny Rachitsky (including Rahul Vohra, Elena Verna, Shreyas Doshi, Brian Chesky, and Gustaf Alströmer).

### Key Capabilities
- **Strict Grounded Q&A**: Answers are grounded **only** in real Lenny podcast transcripts. If the knowledge base does not contain the answer, the assistant clearly states the limitation rather than hallucinating.
- **Verifiable Source Citations**: Every response displays exact episode names, speaker roles, excerpt quotes, relevance scores, and direct podcast URLs.
- **Session Isolation**: Independent chat sessions with persistent conversational context in PostgreSQL (or auto-fallback SQLite).
- **Ship 30 for 30 Skill**: Dedicated agent synthesizing conversation insights into a structured, skimmable ~1,250-word atomic essay (hook, narrative arc, frameworks, and actionable playbook).
- **Artifact Generator & Secure Sandbox Viewer**: Generates Markdown specifications or responsive HTML/CSS prototypes, rendered inside an isolated cross-origin iframe with code inspection.

---

## 🏗️ Architecture & Technology Stack

```
                        +-------------------------------+
                        |       Streamlit Frontend      |
                        |   - ChatGPT-like Chat UI      |
                        |   - Collapsible Source Cards  |
                        |   - Sandboxed Artifact Viewer |
                        +---------------+---------------+
                                        | HTTP REST (port 8000)
                                        v
                        +-------------------------------+
                        |        FastAPI Backend        |
                        |   - Session Management        |
                        |   - Agent & Skill Router      |
                        |   - Vector Retrieval Service  |
                        |   - Provider Abstraction      |
                        +-------+---------------+-------+
                                |               |
                +---------------+               +---------------+
                v                                               v
+-------------------------------+               +-------------------------------+
|     PostgreSQL / pgvector     |               |         LLM Providers         |
|   - Sessions & Messages       |               |   - Ollama (Local Daemon)     |
|   - Ingested Transcript Chunks|               |   - OpenRouter (Cloud API)    |
|   *(with auto SQLite fallback)|               +-------------------------------+
+-------------------------------+
```

- **Frontend**: Streamlit 1.57+ with custom responsive CSS, status indicator badges, and component iframe sandboxing.
- **Backend**: FastAPI with async lifespan, Pydantic V2 schemas, CORS middleware, and structured request logging.
- **Database**: PostgreSQL 16 with pgvector (auto-falls back to local SQLite for zero-friction evaluation).
- **Embeddings & Search**: `sentence-transformers` (`all-MiniLM-L6-v2`) with cosine similarity retrieval.
- **Containerization**: Multi-container `docker-compose.yml` (Postgres, Backend, Frontend).

---

## 📋 Prerequisites

- **Python**: 3.10+ (Tested on Python 3.11.9)
- **Ollama**: Installed locally from [ollama.com](https://ollama.com) (for local LLM execution)
- **Docker & Docker Compose**: (Optional, for containerized run)

---

## ⚙️ Environment Configuration

Copy the example environment file and configure variables:

```bash
cp .env.example .env
```

### Environment Variables Guide
| Variable | Description | Default / Example | Required? |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | Active LLM provider (`ollama` or `openrouter`) | `ollama` | **Yes** |
| `OLLAMA_BASE_URL` | Base URL of local Ollama instance | `http://localhost:11434` | If using Ollama |
| `OLLAMA_MODEL` | Ollama model name to query | `llama3.2` | If using Ollama |
| `OPENROUTER_API_KEY` | OpenRouter API Key | `sk-or-v1-...` | If using OpenRouter |
| `OPENROUTER_MODEL` | Model ID on OpenRouter | `meta-llama/llama-3.3-70b-instruct` | If using OpenRouter |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/lenny_growth` | Optional (auto-fallback to SQLite) |
| `EMBEDDING_MODEL` | Hugging Face embedding model | `all-MiniLM-L6-v2` | No |
| `RAG_TOP_K` | Number of chunks to retrieve per query | `4` | No |
| `RAG_SCORE_THRESHOLD`| Minimum cosine similarity score | `0.20` | No |

*Note: The application never logs secrets or exposes API keys.*

---

## 🦙 Ollama Setup (Mandatory for Demo)

Ollama is the mandatory local provider for offline, private inference.

1. **Download & Install Ollama**:
   - Download the installer from [https://ollama.com/download](https://ollama.com/download).
2. **Pull an LLM Model**:
   - For fast local execution on modern laptops, we recommend:
     ```bash
     ollama pull llama3.2
     ```
   - Alternatively, you can use `mistral`, `llama3`, or `qwen2.5`:
     ```bash
     ollama pull mistral
     ```
3. **Start Ollama**:
   ```bash
   ollama serve
   ```
   *(On macOS/Windows, opening the Ollama desktop app automatically starts the service on `http://localhost:11434`).*
4. **Verify Ollama is Running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

## 🚀 Running Locally (Without Docker)

You can run the backend and frontend locally in two terminal tabs:

### 1. Clone the Repository & Install Dependencies
```bash
git clone https://github.com/naveen-111q/lenny-growth-assistant.git
cd lenny-growth-assistant
pip install -r requirements.txt
```

### 2. Ingest Transcripts (Runs Automatically on Startup, or Manually)
```bash
python -m app.rag.ingestion
```

### 3. Start the FastAPI Backend
```bash
python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Start the Streamlit Frontend
In a separate terminal:
```bash
streamlit run app/frontend/streamlit_app.py --server.port 8501
```
Open your browser at **[http://localhost:8501](http://localhost:8501)**.

---

## 🐳 Running with Docker Compose

For a complete reproducible environment with PostgreSQL + pgvector:

```bash
git clone https://github.com/naveen-111q/lenny-growth-assistant.git
cd lenny-growth-assistant
docker compose up --build
```

### Connecting to Host Ollama from Docker
Inside Docker Compose, the backend container uses:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
```
Ensure Ollama is running on your host machine (`ollama serve`), and the container will automatically route requests to it!

Access endpoints:
- **Frontend App**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧠 Transcript Ingestion & RAG Knowledge Pipeline

The knowledge base contains curated Lenny Podcast transcripts in `data/transcripts/`:
1. **Rahul Vohra** (Superhuman): The 40% PMF benchmark rule, High-Expectation Customer (HXC) persona, and the 4-step PMF engine.
2. **Elena Verna** (Dropbox/Miro): B2B Product-Led Growth, collaborative growth loops vs sales funnels, freemium paywall gates.
3. **Shreyas Doshi** (Stripe/Twitter): High agency mental model, LNO framework (Leverage, Neutral, Overhead tasks).
4. **Brian Chesky** (Airbnb): Founder Mode vs Manager Mode, weekly CEO product reviews, the 11-Star Experience thought exercise.
5. **Gustaf Alströmer** (Y Combinator): Retention curves as the foundation of growth, 4 compounding loops (viral, content, paid, sales).

### Pipeline Steps:
1. **Load & Clean**: `clean_text()` strips non-printable characters and normalizes paragraph formatting.
2. **Chunking**: `chunk_text()` splits transcripts into ~200-word windows with ~35-word overlap, preserving sentence cohesion.
3. **Embedding**: Generates 384-dimensional normalized dense vectors using `all-MiniLM-L6-v2`.
4. **Retrieval**: `retrieve_relevant_chunks()` performs cosine similarity filtering with score thresholding.
5. **Prompt Injection**: Injects retrieved excerpts with strict system instructions prohibiting ungrounded speculation.

---

## ⚡ Specialized Skills & Artifact Viewer

### 1. Ship 30 for 30 Skill (`agents/ship30_skill.py`)
- Transforms conversational insights into a ~1,250-word atomic essay.
- Adheres to Ship 30 digital writing architecture:
  - **Hook**: Attention-grabbing opening statement.
  - **Narrative Progression**: The Trap -> The Mental Shift -> The Core Framework -> The 4-Step Playbook -> Parting Reflection.
  - **Skimmability**: Headers, bullets, and selective bolding.
- Trigger via sidebar button or prompt: *"Write a 1250-word Ship 30 essay on finding product-market fit"*.

### 2. Artifact Generator & In-App Viewer (`agents/artifact_skill.py`)
- Generates **Markdown** strategy documents / PRDs or **HTML/CSS** responsive prototypes.
- **Security & Isolation Architecture**:
  - **Sanitization**: Strips dangerous `<script>` tags, inline handlers (`onerror=`, `onload=`), and `javascript:` pseudoprotocols.
  - **Sandboxing**: Rendered inside an isolated cross-origin iframe using `st.components.v1.html`.
  - **Protection**: Untrusted code cannot access parent application cookies, `localStorage`, or the Streamlit DOM.
  - **Code Inspector**: Evaluator toggle to view formatted raw source code and download the artifact file.

---

## 🔀 Model Provider Switching

Switch models in real time without modifying code:
1. In the Streamlit sidebar, select **Ollama (Local)** or **OpenRouter (Cloud)**.
2. The UI pings `/health` and updates the provider badge (`🟢 ONLINE` or `🔴 UNAVAILABLE`).
3. If Ollama is selected but offline, an actionable troubleshooting guide is displayed.
4. You can override the model name on-the-fly (e.g., `llama3.2`, `mistral`, `claude-3-5-sonnet`).

---

## 🧪 Automated Testing

The project includes an automated test suite covering all mandatory requirements:

```bash
python -m pytest tests/ -v
```

### Tested Capabilities
- `test_health.py`: Verifies `/health` endpoint, DB status, and chunk counter.
- `test_sessions.py`: Verifies session creation, message persistence, and session isolation.
- `test_providers.py`: Verifies Ollama/OpenRouter health checks, generation mocks, and missing key handling.
- `test_rag_retrieval.py`: Verifies text chunking, semantic retrieval for Lenny topics, and empty retrieval on irrelevant queries.
- `test_chat.py`: Verifies `/chat` endpoint, source citation schemas, and conversational history.
- `test_ship30_skill.py`: Verifies ~1,250-word essay generation structure and headers.
- `test_artifact_skill.py`: Verifies Markdown and HTML/CSS artifact generation.
- `test_security.py`: Verifies XSS sanitization (scripts, event handlers, iframe stripping) and secret masking.

---

## 🔍 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Ollama Unavailable` in UI | Ollama daemon is not running | Run `ollama serve` in terminal, or open the Ollama desktop app. |
| `Model not found in Ollama` | Target model not pulled | Run `ollama pull llama3.2` (or set `OLLAMA_MODEL` in `.env`). |
| `OpenRouter 401 Unauthorized` | Invalid or missing API key | Add `OPENROUTER_API_KEY=sk-or-v1-...` to `.env` and restart backend. |
| `PostgreSQL Connection Refused` | Local Postgres is not running | The backend automatically falls back to local SQLite with zero downtime. Alternatively, start Postgres or run via `docker compose up`. |
| Port 8000/8501 in use | Another process occupies port | Terminate the process or adjust `BACKEND_PORT` / `FRONTEND_PORT` in `.env`. |

---

## ⚖️ Discovery, Tradeoffs & Known Limitations

1. **Hallucination Mitigation**: The assistant relies on high cosine similarity thresholds and strict system prompts. If a query falls outside the podcast topics, the assistant explicitly states the limitation rather than guessing.
2. **Local LLM Latency**: Smaller local models (e.g. `llama3.2:1b` or `llama3.2:3b`) offer fast ~1-3s responses, while 8B+ models depend on local GPU acceleration.
3. **HTML Sandboxing**: HTML artifacts are sanitized and isolated inside cross-origin iframes. Network fetching inside the artifact iframe is restricted for evaluation safety.
4. **Offline Resilience**: The RAG pipeline uses local SentenceTransformers (`all-MiniLM-L6-v2`), enabling 100% offline retrieval and local inference without any external API dependencies.
