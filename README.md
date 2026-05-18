# Dash — Autonomous Consumer AI Agent

> Natural language in. Real-world action out.

Dash is an autonomous AI agent built on **Google Cloud Agent Builder** with **Gemini** as the reasoning engine. It moves beyond chat to plan, execute, and complete multi-step real-world tasks — booking travel, scouting gifts, creating accounts, and managing social media — while keeping humans in control at every critical checkpoint.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What Dash Does

| Mission | Description |
|---------|-------------|
| ?? **Global Gift Scout** | Finds & ships the perfect gift internationally, checking social context and logistics constraints automatically |
| ?? **Travel Concierge** | Spawns 3 parallel scouts (flights, hotels, Airbnb) to find the best package deals on the best dates |
| ?? **Account Manager** | Creates, manages, and secures accounts across any platform using ARIA-based DOM navigation |
| ?? **Social Manager** | Brainstorms, schedules, and auto-publishes content across platforms as a permanent workflow |

---

## The 5-Phase Mission Cycle

```
Find ? Read ? Type ? Check ? Save
```

1. **Find** — Locate the right pages and options across the web
2. **Read** — Deconstruct DOM text, map fields via ARIA labels, strip fluff
3. **Type** — Enter details with real browser events, create accounts, prepare carts
4. **Check** — Human-in-the-Loop gate for CAPTCHA, MFA, and payment
5. **Save** — Store receipts, credentials, and context in the MongoDB Mission Vault

---

## Partner Integrations (MCP)

| Partner | MCP Superpower |
|---------|---------------|
| ?? **MongoDB** | Mission Vault — durable user memory, preferences, account references, mission state |
| ?? **GitLab** | Mission Script library — versions and audits every execution plan |
| ?? **Elastic** | Action Search — millisecond recall of previously solved DOM structures |
| ??? **Arize** | Reasoning Observability — monitors agent health and form-fill success rates |
| ?? **Fivetran** | Data Pipeline — streams mission events to the user data warehouse |

---

## Architecture

```
User (Natural Language)
        ¦
        ?
  Dash-1 Master Agent (Gemini)
        ¦
   +---------+
   ¦  MongoDB Mission Vault  ¦?-- Preferences, addresses, account refs
   +---------+
        ¦ spawns
   +--------------------------+
   ¦   Sub-Agents             ¦
   ¦  · Product Scout         ¦
   ¦  · Travel Scout (×3)     ¦
   ¦  · Price/Logistics Agent ¦
   ¦  · Account Resolver      ¦
   ¦  · Social Manager        ¦
   +--------------------------+
        ¦
        ?
  HITL Gate (CAPTCHA / MFA / Payment)
        ¦
        ?
  Action Complete ? Saved to Vault
```

---

## User Stories

### Persona A — The Gift Sender
> "I want to send a gift for my nephew in Trinidad. He has social media. I want suggestions and the best prices."

Dash checks the vault, skips vendors that don't ship to Trinidad, scouts products using social context, ranks by fit/price/delivery confidence, builds the cart, and stops for approval.

### Persona B — The Traveller
> "Best rates for flights, best dates, package deals with hotels and Airbnb."

Dash spawns 3 parallel Travel Scouts, reads live DOM from booking sites, synthesizes the cheapest date windows and package combinations, then books on command.

---

## Running Locally

```bash
# Install backend dependencies
pip install -r requirements.txt

# Start the API server
python api/index.py

# Serve the frontend
# Open index.html in a browser or use a static server
```

API runs on `http://localhost:8000`. The frontend auto-detects local vs. hosted API.

---

## Safety & Privacy

- **No raw passwords stored** — only vault references and authorized session tokens
- **HITL gates** — CAPTCHA, MFA, phone/email verification always pause for human input
- **Payment gate** — purchases never executed without explicit user confirmation
- **Social context by consent** — OAuth or user-approved exports only; no scraping credentials
- **Deleteable context** — every vault entry has source, scope, expiry, and deletion metadata

---

## Hackathon Submission

- **Track:** MongoDB (primary) + GitLab, Elastic, Arize, Fivetran
- **Challenge:** Building Agents for Real-World Challenges — Everyday Consumer Verticals
- **Built with:** Google Cloud Agent Builder · Gemini · MongoDB MCP · GitLab MCP · Elastic MCP · Arize MCP · Fivetran MCP

---

## License

MIT — see [LICENSE](LICENSE)
