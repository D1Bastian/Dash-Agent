# Dash Agent

Dash Agent is a minimalist action agent for real-world browser missions. The user sees a clean ChatGPT-style command surface; the orchestration layer handles discovery, planning, form filling, verification checkpoints, and partner sync in the background.

MongoDB is the first stop in the lifecycle. Dash registers the user into a Mission Vault, records consented context sources, and then Dash-1 routes work to lightweight sub-agents for gifts, flights, account creation, social context, shopping, and DevOps sync.

## Hackathon Track

The primary submission track is **MongoDB**.

Core stack:

- **Gemini 3:** reasoning, planning, and sub-agent orchestration.
- **MongoDB:** Mission Vault for user registration, consent, account context, and mission memory.
- **Elastic:** Action Search for recalling prior DOM and task patterns.
- **Arize:** reasoning observability, guardrails, and mission health.
- **Fivetran:** mission event pipeline for analytics and long-running optimization.

First demo mission:

> Register a user-owned GitLab account, stop for CAPTCHA/email verification when required, then store the mission state in MongoDB and stream the result through the sponsor pipeline.

Follow-up mission:

> Ask whether the user wants to connect GitHub, then sync selected GitHub repositories into GitLab through a consented connection flow.

This aligns with the challenge because Dash does not only answer questions. It opens a live service, maps the page by accessible form semantics, performs controlled browser actions, verifies the resulting state, stores durable context in MongoDB, recalls patterns with Elastic, observes reasoning with Arize, and streams mission data through Fivetran.

## Sponsor Integrations

Dash now shows all five sponsor roles in the mission API:

- **MongoDB:** registers users, stores consented mission state, account context, and profile references.
- **Elastic:** recalls prior DOM/action patterns for resilient form mapping.
- **Arize:** logs reasoning traces, guardrail decisions, and mission health.
- **Fivetran:** streams mission events such as registration checkpoints, account resolution, GitHub sync, and gift scouting into analytics.
- **GitLab:** first real-world target service and optional DevOps sync destination.

## Master/Sub-Agent Architecture

Dash is designed so one master agent can route many consumer missions to focused sub-agents:

- `Identity Registrar`: creates the MongoDB Mission Vault profile.
- `Context Seeder`: attaches approved Google, Apple, GitHub, social, travel, shopping, and manual preference sources.
- `Mission Router`: chooses the lightest useful worker agents for each request.
- `Consent Broker`: confirms what user data can be used.
- `Social Context Scout`: reads public links, user exports, or user-approved browser sessions.
- `Preference Inference`: turns allowed context into interests, constraints, and confidence.
- `Product Scout`: searches merchants and marketplaces.
- `Price And Logistics`: compares landed cost, shipping speed, and seller reliability.
- `Gift Ranker`: scores fit, price, novelty, and delivery confidence.
- `Checkout Prep`: prepares the cart and stops before payment.
- `Connection Broker`: asks for Google, Apple, GitHub, or social context through OAuth, browser handoff, uploads, public links, or a questionnaire.
- `Account Resolver`: checks whether the user already has an account for a service, asks before creating one, and resumes after human verification.
- `Text DOM Deconstructor`: uses visible text, accessible names, ARIA roles, and semantic input types instead of brittle CSS selectors, screenshots, or user-visible JavaScript snippets.

For social networks, Dash does **not** store raw Instagram or Facebook passwords. A user can connect through a supported OAuth flow, complete a browser session handoff, paste public links, upload an export, or answer a short fallback questionnaire.

For Google, Apple, and GitHub, Dash asks the user to connect an account or provide an approved token/export. It does not ask for the account password.

For commerce flows such as Amazon, Dash first checks the Mission Vault for approved account context. Existing credentials are represented as authorized vault or session references, never raw values in chat or logs. If no account exists and the user approves account creation, Dash fills the registration flow and pauses for CAPTCHA, MFA, email, or phone verification. It does not bypass those gates.

See `docs/DOM_DECONSTRUCTION.md` for the text-only form mapping protocol.

Example consumer mission:

> Buy a gift for my friend using allowed context, best price, and delivery confidence.

If the user has no social context available, Dash asks for age range, relationship, occasion, budget, interests, and shipping destination.

## Current Demo Flow

1. The user signs in with email, Google, or Apple.
2. Dash registers the user and consent metadata in MongoDB Mission Vault.
3. The user enters: `Register my GitLab account and provision my mission repo.`
4. Dash opens GitLab registration with Playwright.
5. Dash fills first name, last name, username, email, and password using visible focused fields and browser events.
6. Dash halts at CAPTCHA, MFA, or email verification.
7. After the human checkpoint, Dash resumes and syncs the mission script through GitLab MCP.

## Safety

Dash does not bypass CAPTCHA, MFA, email verification, rate limits, or terms gates. Secrets are never printed; logs mask email, password, tokens, and credentials.

## Run The UI

The frontend is static:

```powershell
start index.html
```

## Run The Backend

```powershell
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

By default, partner MCP calls run in dry-run mode so the demo is safe to test:

```powershell
$env:DASH_MCP_MODE="dry-run"
```

To connect a live MCP gateway, set:

```powershell
$env:DASH_MCP_MODE="live"
$env:DASH_MCP_GITLAB_HTTP_URL="http://localhost:PORT/mcp"
$env:DASH_MCP_GITLAB_TOKEN="..."
```

Useful local checks:

```powershell
Invoke-RestMethod http://localhost:8000/architecture
Invoke-RestMethod -Method Post -Uri http://localhost:8000/users/register -ContentType "application/json" -Body '{"user_id":"demo-user","primary_email":"demo@example.com","auth_provider":"email","authorized_sources":["manual"],"mission_goals":["gitlab-registration","gift-scout","travel"]}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/context/intake -ContentType "application/json" -Body '{"user_id":"demo-user"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/account-resolver -ContentType "application/json" -Body '{"user_id":"demo-user","service_name":"Amazon","service_url":"https://www.amazon.com","account_creation_allowed":false}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/gift-scout -ContentType "application/json" -Body '{"user_id":"demo-user"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/gitlab-registration -ContentType "application/json" -Body '{"user_id":"demo-user","verification_completed":false}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/github-sync -ContentType "application/json" -Body '{"user_id":"demo-user","github_connection_ready":false}'
```

## Run The GitLab Browser Mission

```powershell
python -m playwright install chromium

$env:DASH_GITLAB_FIRST_NAME="YourFirstName"
$env:DASH_GITLAB_LAST_NAME="YourLastName"
$env:DASH_GITLAB_USERNAME="dash-demo-yourname"
$env:DASH_GITLAB_EMAIL="you@example.com"
$env:DASH_GITLAB_PASSWORD="your-password"

python missions\gitlab_registration.py
```

## Repository Checklist

- Public repository
- `LICENSE` file at repository root
- Hosted project URL
- Three-minute demo video
- MongoDB partner track selected on Devpost
