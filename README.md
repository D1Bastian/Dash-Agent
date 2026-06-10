# Dash — AI That Doesn't Just Answer. It Acts.

**Live Demo → [https://dash-agent.onrender.com](https://dash-agent.onrender.com)**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Built with Gemini](https://img.shields.io/badge/Powered%20by-Gemini%202.5-blue)](https://ai.google.dev)
[![MongoDB](https://img.shields.io/badge/Partner-MongoDB-brightgreen)](https://www.mongodb.com)
[![Elastic](https://img.shields.io/badge/Partner-Elastic-yellow)](https://www.elastic.co)
[![GitLab](https://img.shields.io/badge/Partner-GitLab-orange)](https://gitlab.com)
[![Arize](https://img.shields.io/badge/Partner-Arize-purple)](https://arize.com)

---

<table>
  <tr>
    <td width="50%"><img src="docs/images/command-center.png" alt="Dash command center — chat interface with mission cards" width="100%"/></td>
    <td width="50%"><img src="docs/images/architecture.png" alt="Dash agent architecture — Gemini master agent routing to partner superpowers" width="100%"/></td>
  </tr>
  <tr>
    <td align="center"><sub>The command surface — clean, conversational, action-oriented</sub></td>
    <td align="center"><sub>Under the hood — Gemini orchestrating MongoDB, Elastic, GitLab, Arize &amp; Fivetran</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/login-screen.png" alt="Dash login — Google OAuth and demo entry" width="100%"/></td>
    <td width="50%"><img src="docs/images/mission-flow.png" alt="Dash mission lifecycle — Discover, Plan, Form Fill, Verify, Sync" width="100%"/></td>
  </tr>
  <tr>
    <td align="center"><sub>Identity verified by consent — Google OAuth or demo login</sub></td>
    <td align="center"><sub>The 5-phase mission lifecycle with human checkpoint gate</sub></td>
  </tr>
</table>

---

## 🏆 Hackathon Submission Checklist

✅ **Real Gemini Key (Settings API)**: The `/api/set-key` endpoint is live in `backend/main.py`. The frontend function `saveGeminiKey` is in `app.js` and securely validates and stores the judge's key for the session.
✅ **X-Gemini-Key Header**: The header is successfully injected into all fetch requests in `app.js`, and extracted in the FastApi routes (`client_key = request.headers.get("X-Gemini-Key", "")`) before being passed to the Gemini functions.
✅ **Real Fivetran API**: `superpowers/fivetran_pipeline.py` now includes the `list_connectors` method which hits the actual `https://api.fivetran.com/v1/connectors` endpoint.
✅ **README — Judge-First**: The README has been rewritten and includes "Path A" (30 seconds via Demo Login) and "Path B" (Full test locally).
✅ **Partner Table in README**: The partner table correctly displays the "Status" column (🟢 Connected / 🟡 Configurable).

---

## What Is Dash?

Most AI tools are question-answering machines. Dash is different.

Dash is a **real-world action agent** — a minimalist command surface powered by Gemini 2.5 that can plan, remember, browse, fill forms, register accounts, scout products, compare flights, and stop precisely when a human needs to be in the loop. It doesn't simulate these actions. It uses a live Playwright-driven browser, Gemini's reasoning, and a network of partner superpowers to actually *do things* on the web under your oversight.

The design philosophy is **"Silent Power"**: the interface stays clean and conversational, all the heavy orchestration happens invisibly in the background, and you only see high-level outcomes — never raw DOM dumps, telemetry, or logs.

---

## What Dash Can Do

| Mission | What happens |
|---------|-------------|
| **Account Resolver** | Navigates to any registration or login page, uses Gemini to semantically map the form fields, fills them with approved profile data, and pauses at CAPTCHA, MFA, or email verification |
| **Gift Scout** | Uses consented context (interests, age, budget, relationship), applies international shipping constraints, and ranks gift options by interest fit, price confidence, seller reliability, novelty, and delivery risk |
| **Travel Concierge** | Plans flights, stays, dates, and package deals with full awareness of home airport, budget, and passport constraints — stops before booking |
| **Shopping Scout** | Compares products with landed cost, return risk, international shipping availability, and checkout readiness |
| **Social Manager** | Drafts campaigns, content calendars, and posting schedules — stops before publishing without explicit approval |
| **Workflow Architect** | Designs durable recurring workflows with trigger conditions, tool steps, checkpoints, and autonomy levels |

---

## The Mission Lifecycle

Every Dash task runs through five phases, displayed live in the UI:

```
Find → Read → Prepare → Check → Save
```

1. **Find** — Route the request, locate the right pages or services, load user context from MongoDB
2. **Read** — Deconstruct visible text, ARIA roles, labels, placeholders, form hierarchy, and button semantics using Playwright
3. **Prepare** — Ask Gemini to map fields to approved profile keys, fill forms, draft content, or shortlist options
4. **Check** — Pause immediately for CAPTCHA, MFA, email/phone verification, payment, publishing, or irreversible changes
5. **Save** — Write high-level mission state, preferences, and non-secret session references back to MongoDB

## For Judges — Quick Start

You don't need to clone the repo or run this locally to test the AI. You can test the full Gemini reasoning engine right on the live site using your own key.

**Path A: Full Live Test (Recommended)**
1. Visit the live URL: [https://dash-agent.onrender.com](https://dash-agent.onrender.com)
2. Click **Demo Login** on the login screen.
3. Click the **Settings** tab in the main navigation.
4. Paste your **Gemini API Key** in the API Keys section and click **Validate & Save**. 
5. *Dash will validate your key live and activate all AI features for your session without a restart.*

**Path B: Run Locally**
1. Clone: `git clone https://github.com/D1Bastian/Dash-Agent.git`
2. Configure: `cp .env.example .env.local` and add your `GEMINI_API_KEY`.
3. Run: `pip install -r requirements.txt && uvicorn backend.main:app`

---

## Partner Superpowers

Dash is built on six partner integrations that turn a smart chat interface into a capable agent. 

| Partner | Superpower | What It Enables | Status |
|---------|-----------|-----------------|--------|
| **MongoDB** | Mission Vault | Durable memory of user preferences, consent, context sources, and mission state. | 🟢 Connected |
| **Elastic** | Action Search | Caches previously solved DOM/form mappings to accelerate form-filling. | 🟡 Configurable |
| **GitLab** | Mission Scripts | Versions and syncs mission execution scripts. | 🟡 Configurable |
| **Arize** | Observability | Traces Gemini reasoning chains and monitors safety guardrails. | 🟡 Configurable |
| **Fivetran** | Data Pipeline | Streams mission event data (price trends, trip costs, scout results). | 🟡 Configurable |
| **Dynatrace** | Runtime Telemetry | Monitors backend health and operational performance. | 🟡 Configurable |

*Note: For the live demo, MongoDB is fully connected as our primary database. Other partner integrations gracefully fallback to dry-run mode if you do not provide API keys in the `.env` file, meaning the app will never crash and will simulate the partner action.*

---

## Architecture

```
User prompt (chat)
  → Dash-1 Master Agent (Gemini 2.5)
  → MongoDB Mission Vault — load user context & memory
  → Mission Router — classify intent & spawn specialist sub-agents
      ├── Account Resolver     (Playwright + Gemini DOM mapping)
      ├── Product Scout        (price, shipping, ranking)
      ├── Travel Concierge     (flight, stay, logistics)
      ├── Gift Scout           (social context + ranked recommendations)
      ├── Social Manager       (draft, schedule, gate before publish)
      └── Workflow Architect   (recurring mission design)
  → Human Checkpoint Gate      (CAPTCHA / MFA / payment / publish)
  → Elastic — cache solved actions
  → MongoDB — save mission state & non-secret session refs
  → Arize — log reasoning trace
```

## Health Check

```bash
curl https://dash-agent.onrender.com/health
curl https://dash-agent.onrender.com/health/partners
```

The `/health` endpoint reports Gemini model, API key status, and which partner integrations are live vs. dry-run. The `/health/partners` endpoint pings each service and returns real latency measurements.

---

## Hackathon Track

**Primary: MongoDB** — The Mission Vault is the backbone of everything Dash does. Without persistent, consented memory, the agent would be stateless and would ask the same questions on every run. MongoDB turns Dash from a one-shot tool into a trusted assistant that compounds its knowledge over time.

**Secondary proof points:** Elastic (action recall), Arize (observability), GitLab (script versioning), Fivetran (event pipeline), Dynatrace (telemetry).

---

## License

MIT — see [LICENSE](LICENSE).
