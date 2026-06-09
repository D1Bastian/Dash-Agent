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

---

## Partner Superpowers

Dash is built on six partner integrations that turn a smart chat interface into a capable agent:

| Partner | Superpower | What It Enables |
|---------|-----------|-----------------|
| **MongoDB** | Mission Vault | Durable memory of user preferences, consent, context sources, and mission state. Dash remembers who you are so it never asks the same question twice |
| **Elastic** | Action Search | Caches previously solved DOM/form mappings. If Dash has filled a form on a site before, it reuses the solution in milliseconds instead of re-querying Gemini |
| **GitLab** | Mission Scripts | Versions and syncs mission execution scripts. Can provision repositories on your behalf via the GitLab API |
| **Arize** | Observability | Traces Gemini reasoning chains, monitors form-fill success rates, and surfaces agent health data |
| **Fivetran** | Data Pipeline | Streams mission event data (price trends, trip costs, scout results) to your data warehouse |
| **Dynatrace** | Runtime Telemetry | Monitors backend health and operational performance in real time |

When credentials are not configured, every integration degrades gracefully to a dry-run mode — the app never crashes, never lies, and always tells you the real status.

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

### Sub-Agent Roster

- Identity Registrar — creates and hydrates the Mission Vault profile
- Context Seeder — connects consented social, travel, and preference data sources
- DOM Deconstructor — maps visible page semantics to a Gemini-readable snapshot
- Form Operator — types with real keyboard/input/change events
- Price & Logistics — compares landed costs and delivery timelines
- GitLab Sync — versions mission scripts and provisions repos
- Observability — sends traces to Arize
- Human Checkpoint Monitor — detects CAPTCHA, MFA, verification, payment prompts and halts

---

## Safety Design

Dash is designed around human oversight, not around autonomy for its own sake.

- **No raw credentials ever leave the client.** Passwords, tokens, and recovery codes are never sent to Gemini, never logged, and never stored as plaintext.
- **Five explicit human gates.** Payment, booking, CAPTCHA, MFA, email/phone verification, publishing, and irreversible account changes always stop for approval.
- **Context by consent.** Social sources use OAuth, public links, user exports, or browser handoff. Dash never asks for raw social media passwords.
- **Silent logs.** Raw DOM structure, CSS selectors, telemetry, and reasoning traces stay behind the curtain. Users see only high-level mission outcomes.

---

## Running Locally

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/infinite-action-agent.git
cd infinite-action-agent
pip install -r requirements.txt
playwright install chromium

# Configure
cp .env.example .env.local
# Fill in your GEMINI_API_KEY, MONGO_URI, etc.

# Run
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` — use **Demo Login** to explore without OAuth setup.

---

## Deployment (Render)

The included [`render.yaml`](render.yaml) defines the full service. After connecting your GitHub repo on [render.com](https://render.com):

1. Set `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com)
2. Set `MONGO_URI` from [MongoDB Atlas](https://cloud.mongodb.com)
3. Set partner keys for Elastic, Arize, Fivetran, GitLab as desired
4. Render auto-deploys on every push

See [`.env.example`](.env.example) for the full list of supported environment variables.

---

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
