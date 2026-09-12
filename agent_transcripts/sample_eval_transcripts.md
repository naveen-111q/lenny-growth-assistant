# Evaluator Demo Transcripts & Verification Guide
## Project: The Lenny Growth Assistant

This document illustrates the expected multi-turn conversational interaction and outputs for the 2–3 minute evaluator demo.

---

### Step 1: Verification of System Health & Provider Status
**Evaluator Action**:
Open browser at `http://localhost:8501`. Observe sidebar badges:
```
Provider: OLLAMA (Local)
Status: 🟢 OLLAMA ONLINE (or 🔴 UNAVAILABLE with clear fix instructions)
Model: llama3.2
Database: Connected (PostgreSQL / SQLite)
```

---

### Step 2: Grounded Q&A on Product-Market Fit
**User Input**:
> "How did Superhuman systematically measure and find product-market fit?"

**Assistant Response**:
> Rahul Vohra (Founder & CEO of Superhuman) created the **Product-Market Fit Engine** using Sean Ellis's leading indicator metric.
>
> ### The 40% Benchmark Rule
> Rather than waiting for qualitative feedback, Superhuman surveyed existing users with one critical question:
> *"How would you feel if you could no longer use the product?"*
> Options:
> 1. Very disappointed
> 2. Somewhat disappointed
> 3. Not disappointed
>
> Startups with strong growth almost universally score **> 40% answering 'Very disappointed'**. When Superhuman first ran this in 2017, their score was only **22%**.
>
> ### The 4-Step PMF Engine
> 1. **Segment to Find Your High-Expectation Customer (HXC)**: Filter respondents who said "very disappointed" by job title and role. For Superhuman, filtering for founders, executives, and managers jumped their baseline from 22% to 33%.
> 2. **Analyze On-The-Fence Users**: Focus exclusively on users who answered *"somewhat disappointed"*. Completely ignore the "not disappointed" crowd to prevent roadmap dilution.
> 3. **Balance the Roadmap (50/50 Rule)**:
>    - Invest 50% of roadmap effort doubling down on what superfans love (speed, shortcuts, aesthetics).
>    - Invest 50% addressing blockers of "somewhat disappointed" users (mobile apps, integrations).
> 4. **Track Across Cohorts**: Superhuman ran this survey quarterly, increasing their score from 22% -> 33% -> 46% -> 58%.

**Sources Displayed in UI**:
```
🎙️ How to Find Product-Market Fit and Measure It
Guest: Rahul Vohra • Founder and CEO of Superhuman (Relevance: 0.82)
Snippet: "When we started Superhuman in 2015, we didn't launch for several years... Ellis benchmarked hundreds of startups... Those that had strong traction almost always had over 40% answering 'very disappointed'..."
Link: https://www.lennysnewsletter.com/p/how-superhuman-built-an-engine-to-find-product-market-fit
```

---

### Step 3: Follow-Up Conversation Context
**User Input**:
> "What about Elena Verna's advice on when to introduce a paywall for B2B PLG products?"

**Assistant Response**:
> Elena Verna emphasizes that offering a freemium plan is merely a pricing model, not true Product-Led Growth (PLG).
>
> ### Core Paywall Principles
> 1. **Never Gate the 'Aha Moment'**: The free tier must deliver fast, single-player value so the user forms an emotional attachment and daily habit loop.
> 2. **Gating Triggers**: Once the habit is formed, introduce paywalls around:
>    - **Collaboration**: Sharing boards, workspaces, or inviting team members (e.g., Miro, Dropbox).
>    - **Enterprise Controls**: SAML/SSO, audit logs, and compliance.
>    - **Volume & Usage**: Storage or API limits.
> 3. **Enterprise Buyers**: Enterprise executives buy software to manage risk, compliance, and centralization—for software their teams are already addicted to using.

**Sources Displayed in UI**:
```
🎙️ The Ultimate Guide to B2B Product-Led Growth and Monetization
Guest: Elena Verna • Head of Growth at Dropbox, Amplitude, Miro advisor (Relevance: 0.81)
Snippet: "Never put your core 'aha moment' behind a paywall. Your free tier must deliver fast, undeniable value to the single player..."
Link: https://www.lennyspodcast.com/the-ultimate-guide-to-b2b-product-led-growth-elena-verna/
```

---

### Step 4: Refusal on Out-of-Domain Question
**User Input**:
> "Can you explain how black hole thermodynamics works?"

**Assistant Response**:
> "Based on the available Lenny Podcast transcripts, there is not enough information to answer this question. My knowledge is strictly grounded in the ingested episodes covering Product-Market Fit (Rahul Vohra), B2B Product-Led Growth (Elena Verna), High Agency and PM skills (Shreyas Doshi), Founder Mode (Brian Chesky), and Growth Loops & Retention (Gustaf Alströmer). Please try asking about one of these topics!"

---

### Step 5: Generating a ~1,250-Word Ship 30 for 30 Essay
**Action**:
Click sidebar button **"Generate Essay"** with custom topic *"The Superhuman Product-Market Fit Engine"*.

**Output**:
- Displays full atomic essay (~1,250 words) with:
  - **Hook**: *"Most founders treat product-market fit like lightning in a bottle: unpredictable, mysterious, and impossible to control. That intuition is dead wrong."*
  - **Part 1: The Trap** (The fallacy of launching early into a leaky bucket).
  - **Part 2: The Mental Shift** (Treating PMF as a leading metric).
  - **Part 3: The 40% Benchmark** (Sean Ellis metric and HXC segmentation).
  - **Part 4: The 4-Step Playbook** (The 50/50 roadmap allocation).
  - **Part 5: The Reflection Question** (*"What percentage of your current product roadmap is spent polishing what your superfans already adore?"*).

---

### Step 6: Artifact Generation & Sandbox Viewer
**Action**:
Click sidebar button **"Build Artifact"** -> Select **HTML/CSS** -> Prompt: *"Create a Product-Market Fit Engine dashboard displaying the 40% rule survey breakdown and the 50/50 roadmap split."*

**Output in Artifact Viewer Tab**:
- **Rendered View**: High-converting, responsive UI with CSS cards, progress meters for the 40% score, and roadmap split widgets rendered inside an isolated iframe.
- **Code Inspector View**: Full syntax-highlighted HTML/CSS source code with download button.
- **Security Notice**: Confirms all `<script>` tags, inline event handlers, and parent window references have been sanitized and isolated.
