# 🔬 Coding Agent Transcripts — Engineering Log
## Project: The Lenny Growth Assistant
*All AI-assisted coding conversations, decisions, and corrections documented here per assignment requirement.*

---

## Session 1 — Project Scaffolding & FastAPI Architecture

**Goal**: Set up the full project structure with FastAPI backend, session persistence, and provider abstraction.

**Agent Prompt**:
> "Create a FastAPI backend for a conversational AI assistant. I need session management (POST /sessions, GET /sessions, GET /sessions/{id}), a SQLAlchemy-based ORM with PostgreSQL + SQLite fallback, and Pydantic V2 schemas. Use dependency injection for DB sessions."

**Agent Output**:
Generated `app/backend/main.py`, `app/backend/database/session.py`, `app/backend/models/db_models.py`, `app/backend/routes/sessions.py`.

**Issue Encountered**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused
```

**Correction Applied**:
> "The database connection fails at startup when Postgres is unavailable. Wrap the engine creation in a try/except block and fall back to SQLite if Postgres is unreachable. Log a WARNING but allow the application to start normally."

**Agent Fix**: Added graceful PostgreSQL → SQLite fallback in `session.py`:
```python
try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("PostgreSQL connection established successfully.")
except Exception as pg_err:
    logger.warning(f"PostgreSQL unavailable ({pg_err}), falling back to SQLite.")
    sqlite_url = "sqlite:///./data/lenny_assistant.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
```

---

## Session 2 — RAG Pipeline: Ingestion & Retrieval

**Goal**: Build transcript ingestion pipeline with dense embeddings and cosine similarity retrieval.

**Agent Prompt**:
> "Build a RAG pipeline. Load JSON transcripts from data/transcripts/, clean the text, chunk it into ~200-word windows with 35-word overlap, generate 384-dim embeddings using sentence-transformers all-MiniLM-L6-v2, and store chunks in SQLAlchemy's transcript_chunks table. Then implement cosine similarity retrieval."

**Issue Encountered**:
Retrieval was returning irrelevant chunks because the similarity threshold was too low:
```
Returned chunk: "... the podcast intro music fades out as Lenny begins the show ..."
Relevance: 0.21
```

**Correction**:
> "Raise the default similarity threshold from 0.20 to 0.25 and add source deduplication so at most 2 chunks from the same episode are returned per query. This prevents one episode dominating the context."

**Agent Fix**: Updated `retrieval.py` to add episode-level diversity:
```python
seen_episodes = {}
for chunk, score in sorted_results:
    episode_count = seen_episodes.get(chunk.episode_id, 0)
    if episode_count >= 2:
        continue
    seen_episodes[chunk.episode_id] = episode_count + 1
    results.append(...)
```

---

## Session 3 — Provider Abstraction Layer

**Goal**: Create a switchable LLM provider layer supporting Ollama and OpenRouter with the same interface.

**Agent Prompt**:
> "Build a BaseLLMProvider ABC with generate() and check_health() methods. Implement OllamaProvider that calls localhost:11434/api/chat and OpenRouterProvider that calls openrouter.ai/api/v1/chat/completions. Add a factory function get_llm_provider(provider_name, model) -> BaseLLMProvider."

**Issue Encountered**:
When the user switched provider to Ollama but the session stored an OpenRouter model ID (`meta-llama/llama-3.3-70b-instruct`), Ollama rejected the request:
```
httpx.HTTPStatusError: 400 Bad Request — model 'meta-llama/llama-3.3-70b-instruct' not found
```

**Correction Applied**:
> "Add model validation logic in get_llm_provider. If the provider is 'ollama' but the model_id contains a '/' (indicating an OpenRouter namespaced model), fall back to the default Ollama model from settings."

**Agent Fix** in `provider_service.py`:
```python
if provider_key == "ollama" and model_id and "/" in model_id:
    logger.warning(f"Model '{model_id}' appears to be an OpenRouter model ID. Falling back to default Ollama model.")
    model_id = settings.ollama_model
```

---

## Session 4 — Ship 30 Skill & Grounded Essay Generation

**Goal**: Build a Ship 30 for 30 essay skill that produces ~1,250-word structured atomic essays.

**Agent Prompt**:
> "Read the Ship 30 for 30 methodology. Build a skill that takes a topic and conversation context, retrieves grounded transcript chunks, and generates an essay with: 1) arresting hook 2) Part 1: Fatal Misconception 3) Part 2: Mental Shift 4) Part 3: Core Framework 5) Part 4: Tactical Playbook 6) Part 5: Reflection Question. Target ~1,250 words."

**Issue Encountered**:
First attempt with Ollama generated only ~400 words — far below the 1,250-word target.

**Correction Applied**:
> "The Ollama num_predict was capped at 280 tokens. Increase max_tokens to 1800 for the Ship 30 skill specifically. Also add explicit word count instruction in the system prompt: 'This essay MUST be approximately 1,250 words. Do not stop writing early.'"

**Agent Fix**: Updated `ship30_skill.py`:
```python
raw_output = llm.generate(
    prompt=prompt,
    system_prompt=SHIP30_SYSTEM_PROMPT,
    temperature=0.55,
    max_tokens=1800   # was 280
)
```

---

## Session 5 — Artifact Viewer: NameError & Blank Iframe

**Goal**: Debug the Artifact Viewer showing "No artifact generated yet" and blank iframe.

**Failure 1: NameError: name 're' is not defined**

The Streamlit runner cached the old bytecode before `import re` was added. The live process raised:
```
NameError: name 're' is not defined
  File "streamlit_app.py", line 784, in <module>
    cleaned_html = re.sub(r"^```(?:html)?\s*", "", cleaned_html, flags=re.IGNORECASE)
```

**Correction**: Replaced all `re.sub()` calls with plain Python string operations that need no imports:
```python
# Before (broken):
cleaned_html = re.sub(r"^```(?:html)?\s*", "", cleaned_html, flags=re.IGNORECASE)

# After (fixed):
if cleaned_html.startswith("```html"):
    cleaned_html = cleaned_html[7:].lstrip("\n").strip()
elif cleaned_html.startswith("```"):
    cleaned_html = cleaned_html[3:].lstrip("\n").strip()
if cleaned_html.endswith("```"):
    cleaned_html = cleaned_html[:-3].rstrip()
```

**Failure 2: Decision tree graph shows blank iframe**

When prompted "Build a graph on decision tree", the LLM generated D3.js/JavaScript code. The `sanitize_html()` function correctly stripped all `<script>` tags, but this left the `<body>` empty — resulting in a blank rendered frame.

**Root Cause**: No instruction to the LLM on *how* to draw diagrams without JavaScript.

**Correction**: Added keyword detection for visual prompts + SVG-specific instruction in the artifact generation prompt:
```python
is_visual_prompt = any(kw in request.prompt.lower() for kw in [
    "graph", "chart", "diagram", "tree", "flowchart", "decision"
])
if is_visual_prompt and artifact_type == "html":
    svg_note = (
        "IMPORTANT: Use pure SVG (rect, circle, line, path, text with markers). "
        "Do NOT use JavaScript, D3.js, Chart.js, or Mermaid."
    )
```

Also updated `ARTIFACT_SYSTEM_PROMPT` with explicit guidance:
> "For decision trees specifically: draw nodes as `<rect>` with `<text>` labels, connect them with `<line>` or `<path>` elements. Include `<marker>` for arrow heads."

**Failure 3: st.rerun() causes "No artifact generated yet"**

After a successful artifact generation, `st.rerun()` was called immediately. On reload, Streamlit re-evaluated the session_state but the sidebar spinner context was gone. Combined with widget state reset, `current_artifact` appeared as `None` to the Artifact Viewer tab.

**Correction**: Removed `st.rerun()` entirely. Now displays a success banner instead:
```python
st.success("✅ HTML artifact ready! → Click the 🎨 Artifact Viewer tab above to view it.")
```

---

## Session 6 — Docker Compose & One-Command Startup

**Goal**: Create docker-compose.yml for one-command startup.

**Agent Prompt**:
> "Create a docker-compose.yml with 3 services: postgres (pgvector/pgvector:pg16), backend (uvicorn), and frontend (streamlit). Backend must wait for postgres healthcheck. Ollama runs on the host machine, so use host.docker.internal."

**Issue Encountered**:
On Linux hosts, `host.docker.internal` is not automatically available.

**Correction**: Added `extra_hosts` mapping to the backend service:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This resolves `host.docker.internal` to the Docker host gateway on all Linux distributions.
