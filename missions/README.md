# GitLab Registration Mission

This mission is the first demo video path for Dash Agent.

It opens GitLab's registration page, maps fields by accessible labels, fills a single user-owned account profile, submits the form, and pauses for CAPTCHA, MFA, or email verification when GitLab asks for a human.

## Required Environment

Set these locally before recording:

```powershell
$env:DASH_GITLAB_FIRST_NAME="YourFirstName"
$env:DASH_GITLAB_LAST_NAME="YourLastName"
$env:DASH_GITLAB_USERNAME="dash-demo-yourname"
$env:DASH_GITLAB_EMAIL="you@example.com"
$env:DASH_GITLAB_PASSWORD="your-password"
```

Do not record your terminal while typing secrets. Set them before the screen capture starts, or use a password manager and crop the terminal.

## Run

```powershell
python -m playwright install chromium
python missions\gitlab_registration.py
```

The script intentionally does not bypass CAPTCHA, MFA, or email confirmation. When a human checkpoint appears, complete it in the browser and press Enter in the terminal so the mission can resume.

## Video Beat

1. Start on the Dash UI and click `GitLab Registration`.
2. Show the browser opening GitLab and filling the form.
3. Pause at any verification prompt and complete it manually.
4. Resume the agent and show the GitLab MCP provisioning step or dry-run trace.
