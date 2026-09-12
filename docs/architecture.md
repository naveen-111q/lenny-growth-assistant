# Technical Architecture Document
## Project: The Lenny Growth Assistant

---

### 1. Component Topology

```
+---------------------------------------------------------------------------------+
|                                STREAMLIT FRONTEND                               |
|   - Chat Interface with Avatar Streams                                          |
|   - Sidebar Session & Provider Controller                                       |
|   - Real-time Health Diagnostics                                                |
|   - Sandboxed Iframe Artifact Viewer                                            |
+----------------------------------------+----------------------------------------+
                                         | HTTP REST (JSON)
                                         v
+---------------------------------------------------------------------------------+
|                                 FASTAPI BACKEND                                 |
|                                                                                 |
|   +-------------------+   +--------------------+   +------------------------+   |
|   |   Route Handlers  |   |    Agent Router    |   |    Session Service     |   |
|   |  - /health        |-->|  - Growth Assistant|-->|  - Isolation By UUID   |   |
|   |  - /sessions      |   |  - Ship 30 Skill   |   |  - Message Persistence|   |
|   |  - /chat          |   |  - Artifact Skill  |   +------------------------+   |
|   |  - /generate/*    |   +--------------------+                |               |
|   +-------------------+             |                           |               |
|                                     v                           v               |
|                       +--------------------------+  +-----------------------+   |
|                       |  RAG & Vector Retrieval  |  |    Database Session   |   |
|                       |  - SentenceTransformers  |  |  - PostgreSQL Pool    |   |
|                       |  - Cosine Search         |  |  - Graceful SQLite    |   |
|                       +--------------------------+  +-----------------------+   |
+-------------------------------------+-------------------------------------------+
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
+------------------------------------+   +------------------------------------+
|       LOCAL OLLAMA DAEMON          |   |       OPENROUTER CLOUD API         |
|   - Base URL: localhost:11434      |   |   - Base URL: openrouter.ai/api    |
|   - Model: llama3.2, mistral       |   |   - Auth: Bearer Token             |
+------------------------------------+   +------------------------------------+
```

---

### 2. Database Schema (PostgreSQL / SQLite)

The database utilizes standard relational tables with UUID primary keys:

#### `sessions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PRIMARY KEY | Session UUID |
| `title` | `VARCHAR(255)` | NOT NULL | Conversation title |
| `provider` | `VARCHAR(50)` | NOT NULL | Default LLM provider |
| `model` | `VARCHAR(100)` | NOT NULL | Selected model name |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

#### `messages`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PRIMARY KEY | Message UUID |
| `session_id` | `VARCHAR(36)` | FOREIGN KEY (sessions.id) | Owning session |
| `role` | `VARCHAR(20)` | NOT NULL | `user`, `assistant`, or `system` |
| `content` | `TEXT` | NOT NULL | Message text |
| `sources` | `JSON` | NULLABLE | Serialized list of citations |
| `created_at` | `DATETIME` | NOT NULL | Message timestamp |

#### `transcript_chunks`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(100)` | PRIMARY KEY | Unique chunk ID (`{episode_id}_{index}`) |
| `episode_id` | `VARCHAR(100)` | INDEX, NOT NULL | Episode identifier |
| `episode_title` | `VARCHAR(255)` | NOT NULL | Episode title |
| `guest` | `VARCHAR(150)` | NOT NULL | Guest name |
| `guest_role` | `VARCHAR(255)` | NULLABLE | Professional role / organization |
| `url` | `VARCHAR(500)` | NULLABLE | Transcript URL |
| `chunk_index` | `INTEGER` | NOT NULL | Positional index in episode |
| `content` | `TEXT` | NOT NULL | Cleaned transcript excerpt |
| `embedding` | `JSON` | NOT NULL | 384-dimensional dense float vector |
| `created_at` | `DATETIME` | NOT NULL | Ingestion timestamp |

---

### 3. API Endpoints Specification

| Method | Path | Request Body | Response Body | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | `{ status, database, providers }` | Returns system readiness and provider status |
| `POST` | `/sessions` | `{ title?, provider?, model? }` | `SessionResponse` | Creates an independent chat session |
| `GET` | `/sessions` | None | `List[SessionResponse]` | Lists recent sessions sorted by activity |
| `GET` | `/sessions/{id}`| None | `SessionDetailResponse` | Returns session history and messages |
| `POST` | `/chat` | `{ session_id, message, provider?, model? }` | `ChatResponse` | Grounded Q&A with citations |
| `POST` | `/generate/ship30`| `{ session_id, topic?, provider?, model? }` | `Ship30Response` | Generates ~1,250-word Ship 30 essay |
| `POST` | `/generate/artifact`| `{ session_id, artifact_type, prompt, provider?, model? }` | `ArtifactResponse` | Generates Markdown or HTML/CSS artifact |

---

### 4. RAG Retrieval Pipeline

1. **Ingestion**:
   - Transcripts stored in `data/transcripts/` as structured JSON.
   - Text is cleaned (`clean_text`) and segmented into ~200-word windows with 35-word overlap (`chunk_text`).
   - Dense embeddings generated via `sentence-transformers` (`all-MiniLM-L6-v2`) yielding 384-dimensional unit vectors.
2. **Query Processing**:
   - Incoming user queries are embedded into a normalized vector $\mathbf{q}$.
   - Cosine similarity $s = \frac{\mathbf{q} \cdot \mathbf{e}}{\|\mathbf{q}\| \|\mathbf{e}\|}$ is computed across all indexed chunks.
   - Chunks exceeding `RAG_SCORE_THRESHOLD` (0.20) are sorted descending, returning top-k (default 4).
3. **Prompt Grounding**:
   - Retrieved chunks are assembled with episode and speaker metadata.
   - Strict system prompt instructs the model to refuse ungrounded speculation if excerpts are empty or insufficient.

---

### 5. LLM Provider Abstraction

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt, system_prompt, history, temperature, max_tokens) -> str: pass
    @abstractmethod
    def check_health(self) -> ProviderHealthStatus: pass
```

- **`OllamaProvider`**:
  - Connects to `OLLAMA_BASE_URL` (default `http://localhost:11434` or `http://host.docker.internal:11434`).
  - Queries `/api/tags` to verify daemon status and model availability.
  - Generates responses via `/api/chat`.
  - Throws structured HTTP 503/504 exceptions with actionable remediation steps if unreachable or timed out.
- **`OpenRouterProvider`**:
  - Connects to `https://openrouter.ai/api/v1/chat/completions`.
  - Uses `OPENROUTER_API_KEY` from `.env`.
  - Handles credit exhaustion (402), unauthorized keys (401), and timeouts (504).

---

### 6. Resilience & Graceful Degradation Strategy
- **Database Availability**: If PostgreSQL is offline on host startup, the engine catches the exception and immediately switches to SQLite (`sqlite:///./data/lenny_assistant.db`), logging a warning. The application starts without interruption.
- **Empty Retrieval**: When queries cannot be answered by Lenny's transcripts, the system returns a polite, pre-formatted limitation response rather than fabricating plausible-sounding falsehoods.
- **Provider Outage**: The Streamlit UI queries `/health` on load and displays an informative banner with step-by-step resolution commands (`ollama run llama3.2`).
