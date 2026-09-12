# Product Requirements Document (PRD)
## Project: The Lenny Growth Assistant

---

## Forward Deployment Discovery Brief

### User & Problem

**Primary User:** Product managers, growth leads, and early-stage founders who regularly reference Lenny Rachitsky's podcast archive for tactical advice on PMF, PLG, hiring, and retention.

**Job-to-be-done:** When preparing a strategic decision or roadmap pitch, I want to instantly retrieve evidence-backed insights from Lenny's best episodes—without spending 30 minutes scrubbing audio transcripts—so I can present a credible, citable argument in my next meeting.

**Pain Removed:** Generic LLMs hallucinate frameworks, misattribute quotes to wrong speakers, and fabricate episode URLs. Manually searching transcripts is slow and non-repeatable. The assistant removes both by grounding every response exclusively in real ingested transcripts.

### Success Metric

> **Primary metric:** ≥ 90% of factual assertions in grounded responses cite an actual ingested chunk (verifiable via the relevance score and source excerpt card displayed in the UI).

> **Secondary metric:** Zero application crashes in an end-to-end evaluation session covering at least 10 diverse queries, 1 Ship 30 essay, and 1 artifact generation request.

### Assumptions (from Incomplete Brief)

| # | Assumption | Reasoning |
| :--- | :--- | :--- |
| 1 | Evaluator has Python 3.10+ or Docker Desktop installed | Minimum runtime requirement for either deployment path |
| 2 | Ollama is installed on the evaluator's local machine | The brief explicitly requires a local LLM demo |
| 3 | 5 curated transcripts are sufficient for a demo knowledge base | Brief did not specify a minimum episode count; 5 covers all 4 topic clusters specified |
| 4 | OpenRouter is an acceptable "cloud provider" implementation | Brief listed "Anthropic Claude or OpenAI" — OpenRouter provides access to both via a single API abstraction |
| 5 | SQLite auto-fallback satisfies the persistence requirement during local demo | PostgreSQL is available in Docker Compose; SQLite eliminates setup friction for evaluators without Docker |
| 6 | A Streamlit frontend satisfies the "deployable AI product" UX requirement | Brief does not specify React/Next.js; Streamlit delivers a production-grade conversational UI |

### Scope Choices

#### In-Scope
- FastAPI backend with Pydantic V2 validation and CORS
- PostgreSQL schema with session + message + transcript_chunk persistence (auto-falls back to SQLite)
- Provider abstraction supporting Ollama (local) and OpenRouter (cloud)
- Dense embedding RAG with `all-MiniLM-L6-v2` and cosine similarity retrieval
- Grounded conversational Q&A with source citations (episode, speaker, score, URL)
- Ship 30 for 30 essay generation (5-part arc, ~1,250 words)
- Markdown and HTML/CSS artifact generation with sandboxed iframe rendering
- Docker Compose one-command setup (postgres + backend + frontend)
- Automated test suite (8 test files covering API, RAG, sessions, security, skills)
- Structured JSON logging for diagnosis of model, retrieval, and DB failures

#### Intentionally Out-of-Scope
| Feature | Reason Excluded |
| :--- | :--- |
| User authentication / SSO | Positioned as an internal company assistant; single-tenant scope |
| Real-time streaming tokens | Adds WebSocket complexity; batch responses are sufficient for the demo |
| Autonomous multi-agent loops | Non-deterministic; increases hallucination risk for a grounded system |
| Fine-tuning / model weight updates | Out of scope for a RAG-grounded knowledge assistant |
| Mobile responsive native app | Streamlit's fluid layout handles laptop/desktop — sufficient for evaluator |

### Risks & Trade-offs

| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **LLM Hallucination** | 🔴 High | Temperature 0.3, strict system prompt prohibiting outside knowledge, similarity threshold gating — returns explicit fallback if no chunk exceeds threshold |
| **Untrusted HTML Execution (XSS)** | 🔴 Critical | Backend `sanitize_html()` strips `<script>` tags, inline event handlers (`onerror`, `onclick`), `javascript:` URIs, and nested iframes; rendered inside Streamlit's cross-origin iframe |
| **Local Model Quality (Ollama)** | 🟡 Medium | `llama3.2` on 8GB RAM produces adequate grounded responses for the 5-episode corpus; complex artifact generation may require the cloud provider |
| **Ollama Daemon Offline** | 🟡 Medium | Health probe on app load displays a clear error banner with step-by-step remediation (`ollama run llama3.2`) |
| **API Cost / Rate Limits** | 🟡 Medium | OpenRouter credit limits clearly documented in `.env.example`; Ollama provides a zero-cost local fallback |
| **Data Leakage** | 🟢 Low | No PII collected; only podcast transcript content and anonymous session UUIDs stored |
| **Database Connection Failure** | 🟡 Medium | Resilient pool catches PostgreSQL failure at startup and switches to SQLite with a log warning |

---

## 1. Overview & Problem Statement

Product managers, founders, and growth practitioners often seek tactical advice across topics like Product-Market Fit, B2B Product-Led Growth, high agency execution, and compounding growth loops. While Lenny Rachitsky's podcast and newsletter archive contains elite operator playbooks, searching and extracting synthesized, actionable advice is tedious and slow. Generic LLMs often hallucinate frameworks, attribute quotes to wrong leaders, or suggest unsubstantiated tactics.

**The Solution:** An internal conversational AI assistant strictly grounded in Lenny's transcript repository. It delivers verifiable citations, preserves conversational context across sessions, generates ~1,250-word Ship 30 for 30 atomic essays, and builds interactive Markdown / HTML artifacts displayed in an in-app sandbox viewer.

---

## 2. Target Users & Personas
1. **Primary: Early & Growth-Stage Founders**: Seeking quantifiable benchmarks for PMF and advice on when to implement paywalls or self-serve models.
2. **Secondary: Product Managers & Growth Leads**: Looking for operational frameworks (such as Shreyas Doshi's LNO model or Gustaf Alströmer's retention loops) to structure roadmaps and team cadence.
3. **Tertiary: Evaluators & Engineering Leads**: Reviewing full-stack AI engineering craft, clean separation of concerns, containerization, and security hygiene.

---

## 3. Goals & Success Metrics
- **Grounding Accuracy**: 100% of factual assertions must originate from ingested transcripts; zero fabricated URLs or phantom guests.
- **Graceful Fallback**: Queries with insufficient transcript evidence must return a clear, explicit limitation statement rather than speculating.
- **Citation Transparency**: 100% of grounded answers must link to episode titles, guests, relevant snippets, and source URLs.
- **Session Isolation**: Complete data isolation across distinct session IDs.
- **Ship 30 Essay Quality**: Generated essays must achieve ~1,250 words following the 5-part Ship 30 structure.
- **Sandbox Security**: Untrusted HTML artifacts must never execute unauthorized scripts or access parent application data.

---

## 4. Assumptions & Prerequisites
- The evaluator has Python 3.10+ installed or Docker Desktop for container execution.
- Ollama is installed on the evaluator's machine to demonstrate local LLM inference.
- The system maintains high availability by automatically falling back to SQLite if a host PostgreSQL daemon is inactive.

---

## 5. Scope

### In-Scope:
- FastAPI backend with Pydantic V2 validation and CORS.
- PostgreSQL database schema with message and session persistence.
- Provider abstraction supporting local Ollama and cloud OpenRouter.
- Chunking, dense embeddings (`all-MiniLM-L6-v2`), and cosine similarity vector retrieval.
- Grounded conversational Q&A with structured citations.
- Specialized Ship 30 for 30 essay generation module (`agents/ship30_skill.py`).
- Specialized Markdown and HTML/CSS artifact generation module (`agents/artifact_skill.py`).
- Streamlit ChatGPT-style UI with real-time provider diagnostics and an in-app sandboxed Artifact Viewer.
- Docker Compose configuration and automated test suite.

### Out-of-Scope:
- User authentication/SSO (designed as an internal company assistant).
- Complex autonomous multi-agent loops that introduce non-deterministic execution.
- In-memory fine-tuning or model weight modifications.

---

## 6. User Flows

```
[User Launches App]
        |
        v
[System Checks DB & Ollama Health] -> (Status Badges Displayed in Sidebar)
        |
        v
[User Enters Question in Chat Input]
        |
        v
[FastAPI /chat Endpoint] -> [Embed Query] -> [Retrieve Relevant Transcript Chunks]
        |
        +---> [Score >= Threshold?]
                 |-- NO  --> [Return Explicit No-Context Fallback Statement]
                 +-- YES --> [Inject Excerpts & Conversation Context into LLM]
                               |
                               v
                     [LLM Generates Grounded Answer]
                               |
                               v
                     [Persist Messages & Return Citations to UI]
                               |
                               v
[User Triggers 'Generate Ship 30 Essay' or 'Generate Artifact']
        |
        v
[Agent Router Dispatches to Skill Module] -> [Generate Structured Output]
        |
        v
[User Views & Inspects Artifact in Sandboxed Streamlit Viewer]
```

---

## 7. Acceptance Criteria
1. **Health Check**: `GET /health` returns HTTP 200 with JSON detailing database connection, chunk count, and Ollama/OpenRouter availability.
2. **Session Creation**: `POST /sessions` allocates a unique UUID and initializes an independent message log.
3. **Grounded Answers**: Chat responses must accurately reference transcript facts and present source citations.
4. **Hallucination Prevention**: Irrelevant queries must yield the fallback refusal message.
5. **Ship 30 Skill**: Produces an essay of ~1,250 words containing a hook, skimmable headings, bullets, and grounded takeaways.
6. **Artifact Viewer**: Renders HTML prototypes inside an iframe with dangerous tags stripped and provides a code inspector mode.
7. **Resilience**: The application must not crash when Ollama is offline or when an invalid API key is supplied; helpful diagnostic messages must be presented.

---

## 8. Risk Assessment & Mitigation
| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **LLM Hallucination** | High | Low generation temperature (0.3), strict system prompts prohibiting outside knowledge, and similarity score gating. |
| **Untrusted HTML Execution** | Critical | Stripping `<script>`, event handlers, and javascript protocols, rendered inside a sandboxed cross-origin iframe. |
| **Ollama Daemon Offline** | Medium | Health probe displays a clear UI banner with step-by-step commands (`ollama run llama3.2`). |
| **Database Connection Failure** | Medium | Resilient connection pool that catches PostgreSQL failure and gracefully falls back to local SQLite. |
