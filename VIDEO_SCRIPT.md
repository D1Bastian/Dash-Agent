# First Demo Video: Autonomous GitLab Registration

Target length: 3 minutes.

## Story

Dash Agent helps a user move from intent to action. In this first demo, the user asks Dash to register a GitLab account. Gemini plans the mission, MongoDB stores the user and mission context, Elastic recalls DOM/action patterns, Arize observes reasoning and guardrails, and Fivetran streams mission events for analytics.

## Recording Plan

Record locally with OBS. Start the backend and the static web app before capture if you want the API-integrated UI responses visible.

### 0:00-0:20 - Problem

Say:

> Most AI apps stop at advice. Dash is an action agent: it can plan a real web mission, operate the browser, and keep a human in control.

> The partner track is MongoDB. It is the Mission Vault that makes the agent personal and durable.

Show the Dash UI.

### 0:20-0:45 - User Registration

Sign in with email, Google, or Apple.

Say:

> Dash first registers me in MongoDB Mission Vault. That gives the master agent a consented context record before it starts creating accounts, buying gifts, booking flights, or syncing repositories.

### 0:45-1:05 - API-Integrated Command

Click `GitLab Registration` or type:

```text
Register my GitLab account, stop for human verification if needed, then provision the mission repository.
```

Say:

> The frontend is backed by our mission API. It shows only mission-level state, while the agent does page discovery, field mapping, and partner sync in the background.

### 1:05-1:45 - Autonomous Browser Fill

Run:

```powershell
python missions\gitlab_registration.py
```

Show GitLab opening and the form being filled.

Say:

> The browser mission does not rely on brittle CSS selectors. It maps the form through accessible labels and verifies each field holds the intended value.

### 1:45-2:10 - Human Checkpoint

If GitLab shows CAPTCHA or email verification, complete it manually.

Say:

> This is intentional. Dash does not bypass CAPTCHA, MFA, or email confirmation. It halts, asks for human help, then resumes from the new browser state.

### 2:10-2:35 - GitLab MCP Sync

Call the backend with verification completed:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/gitlab-registration -ContentType "application/json" -Body '{"user_id":"demo-user","verification_completed":true}'
```

Say:

> Once the session is verified, Dash records the mission state in MongoDB, observes it with Arize, recalls patterns through Elastic, and streams the event through Fivetran. GitLab is the live target service in this first demo.

### 2:35-2:50 - Ask To Sync GitHub

Click the in-app `Sync GitHub` prompt or call:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/missions/github-sync -ContentType "application/json" -Body '{"user_id":"demo-user","github_connection_ready":false}'
```

Say:

> Dash now asks to connect GitHub through OAuth, a token stored in the vault, or a browser session handoff. It never asks for a GitHub password.

### 2:50-3:00 - Close

Say:

> This is the core pattern: natural language in, real-world action out, with human checkpoints, account context by consent, and partner MCP tools making the action durable.

Show the repository README and LICENSE.

## Optional Expansion Line

Say:

> The same account resolver works for services like Amazon. If I already have an account, Dash uses approved account context. If I do not, it asks permission, fills the form through text and accessibility semantics, pauses for CAPTCHA or MFA, then resumes the shopping mission.
