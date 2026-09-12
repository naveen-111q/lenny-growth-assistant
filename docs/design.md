# Design Specification & UI/UX Principles
## Project: The Lenny Growth Assistant

---

### 1. UI/UX Principles & Philosophy
The interface is designed to evoke a modern, high-craft workspace reminiscent of ChatGPT and Claude, while reflecting the podcast's identity.

1. **Information Density with Breathing Room**: Generous padding, clean cards, and high-contrast typography eliminate visual clutter.
2. **Contextual Transparency**: Every AI assertion is backed by visible, collapsible source cards that expose the exact transcript evidence, speaker, and episode link.
3. **Graceful Degraded States**: If a provider or database is offline, the interface communicates status clearly with actionable remediation rather than breaking or freezing.
4. **Immediate Actionability**: Key workflows (creating new chats, generating Ship 30 essays, producing artifacts) are surfaced via persistent sidebar controls and tabbed views.

---

### 2. Color Palette & Typography
- **Background**: Slate dark tones (`#0f172a` body, `#1e293b` container cards) for reduced eye strain during extended reading.
- **Accents**: Deep indigo (`#6366f1`) and violet (`#818cf8`) for brand identity and interactive highlights.
- **Status Indicators**:
  - Emerald Green (`#34d399`): Online and ready.
  - Coral Red (`#f87171`): Service unavailable or action required.
  - Sky Blue (`#38bdf8`): Grounded links and information banners.
- **Typography**: `Plus Jakarta Sans` via Google Fonts, offering legible geometric proportions for both technical specs and long-form essays.

---

### 3. Information Architecture

```
[Main Application Window]
├── Top Brand Header: Logo, Model ID, Active Provider Badge
├── Navigation Tabs:
│   ├── Tab 1: 💬 Conversation (Chat stream, source expanders, prompt input)
│   ├── Tab 2: 🎨 Artifact Viewer (Sandboxed HTML preview, Markdown reader, Code inspector)
│   └── Tab 3: 📚 Knowledge Base (Episode library cards, guest bios, transcript links)
└── Sidebar:
    ├── Primary Action: ➕ New Chat
    ├── Session Switcher Dropdown (Session ID & message counts)
    ├── Model Provider Switcher (Ollama vs OpenRouter)
    ├── Live Provider Diagnostics & Troubleshooting
    └── Skill Triggers:
        ├── ✍️ Generate Ship 30 Essay (Topic input & word count tracker)
        └── 📦 Generate Artifact (HTML/CSS or Markdown builder)
```

---

### 4. Chat Interaction & Source Cards
- **User Messages**: Framed in sleek rounded bubbles with user avatars.
- **Assistant Messages**: Formatted using rich Markdown, headers, bulleted lists, and selective bolding.
- **Grounded Source Cards**:
  - Nested within an expandable accordion (`📚 Grounded Sources (N cited)`).
  - Displays:
    - 🎙️ Episode Title
    - Guest name and corporate role
    - Quote excerpt directly from the transcript
    - Relevance score (cosine similarity metric)
    - Clickable hyperlink directly to the podcast episode

---

### 5. Secure Artifact Viewer Architecture

#### Security Threat Model:
When an LLM generates HTML/CSS, the output must be treated as **untrusted user content**. Malicious or hallucinated code could attempt:
- Cross-Site Scripting (XSS) via injected `<script>` tags.
- Cookie theft (`document.cookie`) or session hijacking.
- Parent frame DOM manipulation (`window.parent` / `top.location`).
- Malicious redirects via `javascript:` links or inline event listeners (`onerror=`).

#### Multi-Layer Defense Strategy:
1. **Backend Sanitization (`sanitize_html`)**:
   - Strips all `<script>` tags and inner content via regex filtering.
   - Cleans all inline event attributes (`onload`, `onclick`, `onerror`, `onmouseover`).
   - Disallows `javascript:`, `vbscript:`, and `data:` pseudoprotocols in `href` and `src`.
   - Removes nested `<iframe>` tags to avoid clickjacking.
2. **Iframe Isolation**:
   - Rendered using Streamlit's `components.html(artifact_content, height=650, scrolling=True)`.
   - Streamlit hosts the HTML component inside a cross-origin iframe. The browser’s Same-Origin Policy strictly isolates the iframe from the host Streamlit window, preventing any access to parent cookies, local storage, or application DOM.
3. **Dual-View Code Inspector**:
   - In addition to the rendered view, an evaluator can toggle **"Code Inspector"** mode to review raw HTML/Markdown source code, copy it, or download it locally.

---

### 6. Accessibility & Responsive Behavior
- Semantic HTML tags (`<article>`, `<header>`, `<div>`).
- High-contrast text compliance (WCAG AA) across all cards and status badges.
- Fluid grid layout adapting cleanly from widescreen monitors down to laptop displays.
