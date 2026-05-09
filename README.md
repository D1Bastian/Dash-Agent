<p align="center">
  <img src="docs/images/login-screen.png" alt="Dash Agent — Login" width="720" />
</p>

<h1 align="center">Dash Agent</h1>

<p align="center">
  <strong>Autonomous browser missions. Human checkpoints. One clean interface.</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#partner-integrations">Partners</a> •
  <a href="#safety">Safety</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/track-MongoDB-00ED64?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB Track" />
  <img src="https://img.shields.io/badge/engine-Gemini_3-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini 3" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+" />
</p>

---

## What Is Dash?

Dash is an AI action agent that **does things on the web for you** — not just answers questions. Give it a mission, and it opens live websites, fills forms, handles logistics, and pauses only when a human checkpoint (CAPTCHA, MFA, payment) requires your input.

You see a clean chat interface. Behind it, a master orchestrator delegates to lightweight sub-agents, stores durable context in MongoDB, recalls DOM patterns from Elastic, observes reasoning with Arize, and streams mission data through Fivetran.

<p align="center">
  <img src="docs/images/command-center.png" alt="Dash Agent — Command Center" width="720" />
</p>

---

## How It Works

Every mission follows a five-phase lifecycle:

<p align="center">
  <img src="docs/images/mission-flow.png" alt="Mission Lifecycle" width="720" />
</p>

| Phase | What Happens |
|-------|-------------|
| **Discover** | Navigate to the target page, read the live DOM structure |
| **Plan** | Map form fields by accessible labels, ARIA roles, and semantic types |
| **Form Fill** | Type into visible, focused fields with real browser events — secrets stay masked |
| **Verify** | Detect CAPTCHA, MFA, or email gates → **pause for human completion** |
| **Sync** | Store mission state in MongoDB, sync outputs through GitLab/Fivetran |

### Demo Mission: GitLab Registration

```
User → "Register my GitLab account and provision my mission repo."
```

1. Dash opens `gitlab.com/users/sign_up` with Playwright.
2. Maps fields by label: First Name, Last Name, Username, Email, Password.
3. Fills each field with real keyboard events. Secrets are masked in all logs.
4. Clicks "Continue" and checks for CAPTCHA/email verification.
5. **Pauses** at any human gate. You complete it, Dash resumes.
6. After verification → creates a GitLab mission repo and syncs the script via MCP.

---

## Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="Dash Agent Architecture" width="720" />
</p>

### Master/Sub-Agent Model

**Dash-1** is the master orchestrator. It classifies each request and spawns only the sub-agents needed:

| Sub-Agent | Role |
|-----------|------|
| **Identity Registrar** | Creates the user profile in MongoDB Mission Vault |
| **Context Seeder** | Attaches Google, Apple, GitHub, social, or manual preference sources |
| **Account Resolver** | Checks existing accounts before creating new ones |
| **DOM Deconstructor** | Maps forms by text, ARIA roles, and semantic input types |
| **Gift Scout** | Finds, ranks, and prepares gift purchases with consent-first social context |
| **Connection Broker** | Handles OAuth, session handoff, or vault-token flows for external services |
| **Checkout Prep** | Builds the cart, stops before payment for explicit approval |

---

## Partner Integrations

Dash integrates five hackathon partner tracks through a unified MCP (Model Context Protocol) bridge:

| Partner | Role in Dash | Module |
|---------|-------------|--------|
| 🟢 **MongoDB** | **Mission Vault** — user registration, consent, account context, and durable mission memory | `superpowers/mongo_vault.py` |
| 🟡 **Elastic** | **Action Search** — millisecond recall of previously solved DOM patterns | `superpowers/elastic_search.py` |
| 🟣 **Arize** | **Reasoning Observability** — traces, guardrails, and mission health monitoring | `superpowers/arize_monitor.py` |
| 🔵 **Fivetran** | **Data Pipeline** — streams mission events into analytics | `superpowers/fivetran_pipeline.py` |
| 🟠 **GitLab** | **Mission Sync** — provisions repos and versions mission scripts | `superpowers/gitlab_sync.py` |

All partner calls go through `superpowers/mcp_client.py`, which defaults to **dry-run mode** for safe local testing.

---

## Quick Start

### 1. Run the UI

The frontend is a static HTML page — no build step required:

```powershell
start index.html
```

### 2. Run the Backend

```powershell
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

By default, partner MCP calls run in **dry-run mode**:

```powershell
$env:DASH_MCP_MODE="dry-run"
```

### 3. Run the GitLab Browser Mission

```powershell
python -m playwright install chromium

$env:DASH_GITLAB_FIRST_NAME="YourFirstName"
$env:DASH_GITLAB_LAST_NAME="YourLastName"
$env:DASH_GITLAB_USERNAME="dash-demo-yourname"
$env:DASH_GITLAB_EMAIL="you@example.com"
$env:DASH_GITLAB_PASSWORD="your-password"

python missions\gitlab_registration.py
```

### 4. Test the API

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/health

# Register a user
Invoke-RestMethod -Method Post -Uri http://localhost:8000/users/register `
  -ContentType "application/json" `
  -Body '{"user_id":"demo","primary_email":"demo@example.com","auth_provider":"email","authorized_sources":["manual"],"mission_goals":["gitlab-registration"]}'

# View the architecture
Invoke-RestMethod http://localhost:8000/architecture
```

<details>
<summary><strong>All API Endpoints</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/architecture` | Full sub-agent architecture map |
| `POST` | `/users/register` | Register user in Mission Vault |
| `POST` | `/context/intake` | Connect data context sources |
| `POST` | `/missions/gitlab-registration` | Run GitLab registration mission |
| `POST` | `/missions/github-sync` | Sync GitHub repos → GitLab |
| `POST` | `/missions/gift-scout` | Gift recommendation mission |
| `POST` | `/missions/account-resolver` | Resolve/create service accounts |

</details>

---

## Project Structure

```
dash-agent/
├── index.html                  # Minimalist chat UI
├── app.js                      # Frontend mission routing and status animations
├── style.css                   # Dark glassmorphism design system
├── backend/
│   ├── main.py                 # FastAPI mission orchestrator (8 endpoints)
│   └── orchestrator.py         # Master/sub-agent planner
├── superpowers/
│   ├── mcp_client.py           # MCP JSON-RPC bridge (dry-run + live)
│   ├── mongo_vault.py          # MongoDB Mission Vault integration
│   ├── elastic_search.py       # Elastic DOM pattern recall
│   ├── arize_monitor.py        # Arize reasoning observability
│   ├── fivetran_pipeline.py    # Fivetran event streaming
│   └── gitlab_sync.py          # GitLab repo provisioning
├── missions/
│   └── gitlab_registration.py  # Playwright browser mission script
├── docs/
│   ├── DOM_DECONSTRUCTION.md   # Text-only form mapping protocol
│   └── MASTER_PROMPT.md        # Agent system prompt reference
├── requirements.txt            # Python dependencies
└── LICENSE                     # MIT
```

---

## Safety

| Guardrail | How It Works |
|-----------|-------------|
| **CAPTCHA / MFA / Email** | Dash detects these gates and **pauses**. It never bypasses them. |
| **Credential Isolation** | Passwords, tokens, and secrets are never printed to logs or chat. The MCP client redacts sensitive fields automatically. |
| **Payment Gate** | Dash prepares carts but **stops before checkout** for explicit user confirmation. |
| **Consent First** | Context sources (Google, Apple, social) require user approval. No raw social passwords are stored. |
| **DOM by Text** | Forms are mapped by visible text, ARIA roles, and semantic types — not brittle CSS selectors. |

---

## Consumer Missions

Beyond GitLab registration, Dash supports multi-vertical consumer missions:

- 🎁 **Gift Scout** — Find gifts using consented friend context, rank by fit/price/delivery, stop before purchase.
- ✈️ **Travel** — Compare flights and stays, handle autocomplete and calendar widgets.
- 🛒 **Shopping** — Resolve accounts, apply international shipping filters, fill multi-field address forms.
- 🔗 **GitHub Sync** — Connect GitHub via OAuth or token, sync selected repos into GitLab.
- 📋 **Account Resolver** — Check for existing accounts, create new ones with form automation, pause at verification.

---

## License

[MIT](LICENSE) — © 2026 Dash Agent contributors

