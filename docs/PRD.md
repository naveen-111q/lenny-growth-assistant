# Product Requirements Document (PRD)
## Project: The Lenny Growth Assistant

---

### 1. Overview & Problem Statement
Product managers, founders, and growth practitioners often seek tactical advice across topics like Product-Market Fit, B2B Product-Led Growth, high agency execution, and compounding growth loops. While Lenny Rachitsky’s podcast and newsletter archive contains elite operator playbooks, searching and extracting synthesized, actionable advice is tedious and slow. Generic LLMs often hallucinate frameworks, attribute quotes to wrong leaders, or suggest unsubstantiated tactics.

**The Solution:** An internal conversational AI assistant strictly grounded in Lenny’s transcript repository. It delivers verifiable citations, preserves conversational context across sessions, generates ~1,250-word Ship 30 for 30 atomic essays, and builds interactive Markdown / HTML artifacts displayed in an in-app sandbox viewer.

---

### 2. Target Users & Personas
1. **Primary: Early & Growth-Stage Founders**: Seeking quantifiable benchmarks for PMF and advice on when to implement paywalls or self-serve models.
2. **Secondary: Product Managers & Growth Leads**: Looking for operational frameworks (such as Shreyas Doshi’s LNO model or Gustaf Alströmer’s retention loops) to structure roadmaps and team cadence.
3. **Tertiary: Evaluators & Engineering Leads**: Reviewing full-stack AI engineering craft, clean separation of concerns, containerization, and security hygiene.

---

### 3. Goals & Success Metrics
- **Grounding Accuracy**: 100% of factual assertions must originate from ingested transcripts; zero fabricated URLs or phantom guests.
- **Graceful Fallback**: Queries with insufficient transcript evidence must return a clear, explicit limitation statement rather than speculating.
- **Citation Transparency**: 100% of grounded answers must link to episode titles, guests, relevant snippets, and source URLs.
- **Session Isolation**: Complete data isolation across distinct session IDs.
- **Ship 30 Essay Quality**: Generated essays must achieve ~1,250 words following the 5-part Ship 30 structure.
- **Sandbox Security**: Untrusted HTML artifacts must never execute unauthorized scripts or access parent application data.

---

### 4. Assumptions & Prerequisites
- The evaluator has Python 3.10+ installed or Docker Desktop for container execution.
- Ollama is installed on the evaluator's machine to demonstrate local LLM inference.
- The system should maintain high availability by automatically falling back to SQLite if a host PostgreSQL daemon is inactive.

---

### 5. Scope

#### In-Scope:
- FastAPI backend with Pydantic V2 validation and CORS.
- PostgreSQL database schema with message and session persistence.
- Provider abstraction supporting local Ollama and cloud OpenRouter.
- Chunking, dense embeddings (`all-MiniLM-L6-v2`), and cosine similarity vector retrieval.
- Grounded conversational Q&A with structured citations.
- Specialized Ship 30 for 30 essay generation module (`agents/ship30_skill.py`).
- Specialized Markdown and HTML/CSS artifact generation module (`agents/artifact_skill.py`).
- Streamlit ChatGPT-style UI with real-time provider diagnostics and an in-app sandboxed Artifact Viewer.
- Docker Compose configuration and automated test suite.

#### Out-of-Scope:
- User authentication/SSO (designed as an internal company assistant).
- Complex autonomous multi-agent loops that introduce non-deterministic execution.
- In-memory fine-tuning or model weight modifications.

---

### 6. User Flows

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

### 7. Acceptance Criteria
1. **Health Check**: `GET /health` returns HTTP 200 with JSON detailing database connection, chunk count, and Ollama/OpenRouter availability.
2. **Session Creation**: `POST /sessions` allocates a unique UUID and initializes an independent message log.
3. **Grounded Answers**: Chat responses must accurately reference transcript facts and present source citations.
4. **Hallucination Prevention**: Irrelevant queries must yield the fallback refusal message.
5. **Ship 30 Skill**: Produces an essay of ~1,250 words containing a hook, skimmable headings, bullets, and grounded takeaways.
6. **Artifact Viewer**: Renders HTML prototypes inside an iframe with dangerous tags stripped and provides a code inspector mode.
7. **Resilience**: The application must not crash when Ollama is offline or when an invalid API key is supplied; helpful diagnostic messages must be presented.

---

### 8. Risk Assessment & Mitigation
| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **LLM Hallucination** | High | Low generation temperature (0.3), strict system prompts prohibiting outside knowledge, and similarity score gating. |
| **Untrusted HTML Execution** | Critical | Stripping `<script>`, event handlers, and javascript protocols, rendered inside a sandboxed cross-origin iframe. |
| **Ollama Daemon Offline** | Medium | Health probe displays a clear UI banner with step-by-step commands (`ollama run llama3.2`). |
| **Database Connection Failure** | Medium | Resilient connection pool that catches PostgreSQL failure and gracefully falls back to local SQLite. |
