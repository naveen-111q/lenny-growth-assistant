# Design Specification & UI/UX Principles
## Project: The Lenny Growth Assistant

---

## 1. UI/UX Principles & Philosophy

The interface is designed as a modern, high-craft light-mode workspace — clean, professional, and immediately trustworthy for product and growth practitioners. The design draws inspiration from Notion, Linear, and Claude's artifact panel.

1. **Information Density with Breathing Room**: Generous padding, clean white cards, and high-contrast indigo accents eliminate visual clutter while surfacing all critical information.
2. **Contextual Transparency**: Every AI assertion is backed by visible, collapsible source cards that expose the exact transcript evidence, speaker, and episode link.
3. **Graceful Degraded States**: If a provider or database is offline, the interface communicates status clearly with actionable remediation steps (e.g., `ollama run llama3.2`) rather than breaking or freezing.
4. **Immediate Actionability**: Key workflows — creating new chats, generating Ship 30 essays, producing artifacts — are surfaced via persistent sidebar controls and tabbed views.
5. **Distinct Role Identity**: User queries and assistant responses use strongly contrasting color-coded bubble backgrounds so the conversation thread is instantly scannable.

---

## 2. Color Palette & Typography

### Light Theme Palette (Active)
| Token | Hex | Usage |
| :--- | :--- | :--- |
| Background | `#f0f4ff` | App background |
| Surface | `#ffffff` | Chat bubbles, cards |
| User Bubble | `linear-gradient(135deg, #4f46e5 → #6366f1)` | User message background (indigo) |
| Assistant Bubble | `linear-gradient(135deg, #059669 → #10b981)` | Assistant message background (emerald) |
| Primary Accent | `#4f46e5` (Indigo-600) | Buttons, active states, links |
| Border | `#e8eaf0` | Card and container dividers |
| Text Primary | `#1e293b` | Body content |
| Text Secondary | `#64748b` | Captions, meta labels |
| Success | `#10b981` (Emerald) | Online status badges |
| Error | `#ef4444` (Red) | Offline banners, error states |
| Warning | `#f59e0b` (Amber) | Partial / degraded states |

### Typography
- **Primary Font**: `Plus Jakarta Sans` (Google Fonts) — geometric humanist, excellent legibility for long-form technical content
- **Fallback Stack**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Base size**: 15px; line-height: 1.65 for sustained reading comfort

---

## 3. Information Architecture

```
[Main Application Window]
├── Top Brand Header: "🎙️ The Lenny Growth Assistant" + active model badge
├── Navigation Tabs (persistent):
│   ├── Tab 1: 💬 Conversation  (Chat stream, source expanders, prompt input)
│   ├── Tab 2: 🎨 Artifact Viewer (Rendered iframe + Code Inspector + Security notice)
│   └── Tab 3: 📚 Knowledge Base (5 episode cards with guest bios and transcript links)
└── Sidebar (always visible):
    ├── ➕ New Chat (creates a fresh session)
    ├── Session Switcher Dropdown (UUID + message count)
    ├── Model Provider Switcher (Ollama / OpenRouter)
    ├── Active Model Display + Live Health Badges
    ├── System Diagnostics (DB status, chunk count, provider latency)
    └── Skill Triggers:
        ├── ✍️ Generate Ship 30 Essay (topic input)
        └── 📦 Generate Artifact (HTML/CSS or Markdown + prompt)
```

---

## 4. Chat Interaction & Source Cards

### Message Bubbles
- **User Messages**: Full-width indigo gradient background `(#4f46e5 → #6366f1)` with white bold text — visually dominant, clearly initiating.
- **Assistant Messages**: Full-width emerald gradient background `(#059669 → #10b981)` with white text — clearly responding, distinct color language.
- Both extend the background color to the full text length (no truncated highlight).

### Grounded Source Cards
Nested within an expandable accordion (`📚 Grounded Sources (N cited)`):
- 🎙️ **Episode Title** (linked to podcast URL)
- Guest name and corporate role
- Verbatim excerpt from the transcript
- **Relevance score** (cosine similarity %)
- Only shown when sources were actually retrieved (hidden when fallback message is returned)

---

## 5. Secure Artifact Viewer Architecture

### Security Threat Model
When an LLM generates HTML/CSS, the output must be treated as **untrusted user content**. Malicious or hallucinated code could attempt:
- Cross-Site Scripting (XSS) via injected `<script>` tags
- Cookie theft (`document.cookie`) or session hijacking
- Parent frame DOM manipulation (`window.parent` / `top.location`)
- Malicious redirects via `javascript:` links or inline event listeners (`onerror=`)

### Multi-Layer Defense Strategy

1. **Backend Sanitization (`sanitize_html` in `artifact_skill.py`)**:
   - Strips all `<script>` tags and inner content via regex
   - Removes all inline event attributes (`onload`, `onclick`, `onerror`, `onmouseover`)
   - Disallows `javascript:`, `vbscript:`, and `data:` pseudoprotocols in `href`/`src`
   - Removes nested `<iframe>` tags to prevent clickjacking
   - Auto-wraps partial HTML in a clean `<!DOCTYPE html>` document shell

2. **Iframe Isolation**:
   - Rendered via `st.components.v1.html(content, height=700, scrolling=True)`
   - Streamlit hosts the component inside a cross-origin iframe; the browser's Same-Origin Policy strictly prevents the iframe from reading parent cookies, localStorage, or application DOM

3. **LLM Instruction-Level Prevention**:
   - System prompt explicitly forbids `<script>` tags
   - For graph/diagram prompts: keyword detection triggers SVG-specific instructions so the LLM draws diagrams using pure `<svg>` elements instead of JavaScript visualization libraries

4. **Code Inspector**:
   - Toggle between Rendered View and Code Inspector to review raw HTML/CSS source before trusting it
   - Security notice banner explicitly lists what is blocked and why

---

## 6. Key Interaction States

| State | Visual Treatment |
| :--- | :--- |
| **Initial load** | Empty chat with welcome assistant message listing capabilities |
| **Typing / pending response** | Streamlit spinner in chat column |
| **Grounded response** | Emerald bubble + collapsible "📚 Grounded Sources" accordion |
| **Fallback / no context** | Emerald bubble with explicit limitation statement; source accordion hidden |
| **Provider offline** | Red warning banner in sidebar with step-by-step fix commands |
| **Artifact ready** | Green success banner with "Click 🎨 Artifact Viewer tab" instruction |
| **Artifact Viewer empty** | Blue info box guiding user to Generate Artifact sidebar tool |

---

## 7. Accessibility & Responsive Behavior

- **Contrast**: Text-on-colored-bubble combinations tested for WCAG AA compliance (>4.5:1 contrast ratio)
- **Semantic HTML**: Streamlit renders `<article>`, `<header>`, `<div>` wrappers; source cards use `<details>`/`<summary>` for accessible accordion behavior
- **Responsive layout**: Streamlit's fluid column system scales from widescreen down to 1280px laptop displays cleanly
- **Screen reader support**: All status badges use text labels (not just icons) — e.g., "🟢 OLLAMA ONLINE" not just a color indicator
