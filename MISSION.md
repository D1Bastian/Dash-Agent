# Dash Agent — Mission Log

## Current Directive

Shift from DevOps demos to everyday consumer challenges. Demonstrate how Dash moves beyond a chatbot to act as a proactive, autonomous orchestrator for complex, multi-step real-world tasks — travel booking, international gifting, account creation, and social media management.

## Core Philosophy: Move Beyond Chat

Dash does not provide links or text answers. Built on Google Cloud Agent Builder with Gemini as the reasoning engine, Dash acts on the user behalf. It plans steps, navigates web pages, deconstructs DOM text, fills forms, and uses sub-agents to do the heavy lifting in the background. It pauses only for human checkpoints: CAPTCHA, MFA, payment confirmation.

## The 5-Phase Mission Cycle

Every mission follows this architecture — invisibly to the user:

| Phase | Label | What Happens |
|-------|-------|-------------|
| 1 | **Find** | Locate the right pages and options across the web |
| 2 | **Read** | Deconstruct DOM text, strip fluff, map fields via ARIA labels |
| 3 | **Type** | Enter details, create accounts, prepare carts securely |
| 4 | **Check** | HITL gate — CAPTCHA, MFA, payment approval |
| 5 | **Save** | Store receipts, credentials, and context to MongoDB Mission Vault |

## Partner Superpowers (MCP Integrations)

| Partner | Role |
|---------|------|
| **MongoDB** | Mission Vault — durable user memory, preferences, account references |
| **GitLab** | Mission Script library — versions and audits execution state |
| **Elastic** | Action Search — millisecond recall of previously solved DOM structures |
| **Arize** | Reasoning Observability — monitors agent health and success rates |
| **Fivetran** | Data Pipeline — streams mission events to the user data warehouse |

## Active Mission 1: Global Gift Scout

**User Request:** "I want to send a gift for my nephew in Trinidad. He has social media — I want suggestions and the best prices."

**Workflow:**
1. Check MongoDB Vault for nephew social context and destination constraints
2. Skip vendors that do not ship to Trinidad automatically
3. Product Scout sub-agent finds items; Price/Logistics agent compares rates
4. Account Resolver creates store account in background if needed
5. **HITL gate** — present ranked options, stop before payment

## Active Mission 2: Travel Concierge

**User Request:** "Best rates for flights, best dates, package deals with hotels and Airbnb."

**Workflow:**
1. Spawn 3 parallel Travel Scout sub-agents (flights, hotels, Airbnb)
2. Agents read live DOM, compare real-time dates and prices
3. Synthesize best package combos using vault preferences (seat type, layover limit, home airport)
4. Present options to user for final approval
5. On "Book it" — handle checkout, passenger details, save itinerary to vault

## Permanent Workflows

Users can create automated agentic workflows:
- **Social Media Manager** — brainstorm with Dash, approve content, set frequency, auto-publish
- **Price Drop Alerts** — monitor products, alert before buying
- **Account Manager** — create and maintain accounts across platforms on request

## Safety Guardrails

- Credentials stored as vault references, never raw secrets
- CAPTCHA, MFA, email/phone verification always pause for human input
- Payment never executed without explicit user confirmation
- Social context (Instagram, Facebook) accessed via OAuth or user-approved exports only
