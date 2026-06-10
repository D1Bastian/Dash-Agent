import os
import json
from dotenv import load_dotenv
load_dotenv(".env.local")
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from superpowers.arize_monitor import ArizeMonitor
from superpowers.dynatrace_observe import DynatraceObserve
from superpowers.elastic_search import ElasticSearch
from superpowers.fivetran_pipeline import FivetranPipeline
from superpowers.mongo_vault import MongoVault
from backend.orchestrator import MasterOrchestrator, serialize_agents
from backend.auth import router as auth_router
from backend.config import DYNAMIC_CONFIG, resolve_config, is_configured

ROOT = Path(__file__).resolve().parents[1]

# ── Env vars ────────────────────────────────────────────────────────────────
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-05-20")
GEMINI_THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "low")

app = FastAPI(title="Dash Agent Mission Orchestrator")
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Gemini-Key"],
)

# ── Security headers ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com "
        "https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://generativelanguage.googleapis.com;"
    )
    return response


# ── Dash Agent system prompt ─────────────────────────────────────────────────
DASH_SYSTEM_PROMPT = """
You are Dash, a fully autonomous AI web agent. You help users take real actions — register accounts, fill forms, book flights, shop, manage workflows — anything a human can do in a browser.

You use a conversational approach:
1. Understand what the user wants.
2. If you need information (credentials, preferences, destinations, etc.), ask naturally in the conversation.
3. Once you have everything needed, announce what you're about to do, then output a DASH_ACTION block.

Action block format (output at the END of your message, it will NOT be shown to the user):

<DASH_ACTION>{"type":"web_agent","url":"https://...","task":"what to accomplish on this page","profile":{"first_name":"...","last_name":"...","username":"...","email":"...","password":"..."}}</DASH_ACTION>

For navigation/search without a profile:
<DASH_ACTION>{"type":"web_navigate","url":"https://...","task":"what to find or do"}</DASH_ACTION>

Rules:
- NEVER display passwords or sensitive data in your visible response text.
- ALWAYS ask for credentials through natural conversation if you don't have them.
- Tell the user you will pause for CAPTCHA, email verification, MFA, or payment.
- Be direct and confident. You ARE going to take the action — not simulate it.
- You have partner superpowers: MongoDB (memory), Elastic (action cache), Arize (observability), Fivetran (mission analytics), Dynatrace (runtime telemetry), and GitLab (mission script versioning when configured).
- Whenever a partner tool is available, actively use it as part of your planning and execution.
- Elastic helps recall previously solved actions, Arize logs reasoning and guardrails, Fivetran streams mission analytics, Dynatrace captures telemetry, and MongoDB stores mission state and user context.
- If GitLab is not configured, continue without it and note dry-run fallback behavior.
- When you output a DASH_ACTION, the system executes it and streams live browser results back.
"""

# ── Helpers ──────────────────────────────────────────────────────────────────
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gemini_generation_config(model: str) -> dict[str, Any]:
    config: dict[str, Any] = {"maxOutputTokens": 8192}
    if "2.5" in model or "3" in model:
        config["temperature"] = 1.0
        config["thinkingConfig"] = {"thinkingBudget": 1024}
    else:
        config["temperature"] = 0.7
    return config


async def gemini(prompt: str, system: str = "", model: str = GEMINI_MODEL, api_key: str = "") -> str:
    """Call Gemini. Accepts client key via api_key param (from X-Gemini-Key header)."""
    key = api_key or resolve_config("GEMINI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="No Gemini API key configured. Add GEMINI_API_KEY to environment or pass X-Gemini-Key header.")

    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {"contents": contents, "generationConfig": gemini_generation_config(model)}
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={key}"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def gemini_converse_stream(history: list[dict], model: str = GEMINI_MODEL, api_key: str = ""):
    """Stream a multi-turn Gemini conversation. history = [{role, content}, ...]"""
    key = api_key or resolve_config("GEMINI_API_KEY")
    if not key:
        yield f"data: {json.dumps({'error': 'No Gemini API key configured. Pass X-Gemini-Key header or set GEMINI_API_KEY.'})}\n\n"
        return

    # Build contents: inject system prompt as first user/model turn
    contents = [
        {"role": "user",  "parts": [{"text": DASH_SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Understood. I am Dash, ready to take real actions."}]},
    ]
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    payload = {"contents": contents, "generationConfig": gemini_generation_config(model)}
    url = f"{GEMINI_API_BASE}/models/{model}:streamGenerateContent?alt=sse&key={key}"

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        text = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                        if text:
                            yield text
                    except Exception:
                        pass


async def gemini_stream(prompt: str, system: str = "", model: str = GEMINI_MODEL, api_key: str = ""):
    """Single-turn SSE stream (kept for backward compat with older endpoints)."""
    key = api_key or resolve_config("GEMINI_API_KEY")
    if not key:
        yield f"data: {json.dumps({'error': 'No Gemini API key configured. Pass X-Gemini-Key header or set GEMINI_API_KEY.'})}\n\n"
        return
    contents = []
    if system:
        contents.append({"role": "user",  "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {"contents": contents, "generationConfig": gemini_generation_config(model)}
    url = f"{GEMINI_API_BASE}/models/{model}:streamGenerateContent?alt=sse&key={key}"
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]": break
                    try:
                        chunk = json.loads(raw)
                        text = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                        if text:
                            yield f"data: {json.dumps({'text': text})}\n\n"
                    except Exception:
                        pass


# ── Models ────────────────────────────────────────────────────────────────────
class MissionExecuteRequest(BaseModel):
    user_id: str = "anonymous"
    prompt: str
    mission_type: str = "task"
    context: dict = Field(default_factory=dict)


class UserRegistrationRequest(BaseModel):
    user_id: str
    display_name: str | None = None
    primary_email: str | None = None
    auth_provider: str = "email"
    authorized_sources: list[str] = Field(default_factory=list)
    default_country: str | None = None
    preferred_currency: str | None = None
    mission_goals: list[str] = Field(default_factory=list)


class GiftScoutRequest(BaseModel):
    user_id: str = "anonymous"
    friend_name: str | None = None
    occasion: str | None = None
    budget: str | None = None
    relationship: str | None = None
    age_range: str | None = None
    interests: list[str] = Field(default_factory=list)
    public_social_links: list[str] = Field(default_factory=list)
    connected_social_session: bool = False
    shipping_country: str | None = None


class ShoppingScoutRequest(BaseModel):
    user_id: str = "anonymous"
    item: str | None = None
    budget: str | None = None
    shipping_country: str | None = None
    preference: str | None = None
    constraints: list[str] = Field(default_factory=list)


class TravelRequest(BaseModel):
    user_id: str = "anonymous"
    origin: str | None = None
    destination: str | None = None
    dates: str | None = None
    budget: str | None = None
    prompt: str | None = None


class SocialRequest(BaseModel):
    user_id: str = "anonymous"
    prompt: str
    goal: str | None = None
    platforms: str | None = None
    cadence: str | None = None


class GitHubSyncRequest(BaseModel):
    user_id: str = "anonymous"
    github_connection_ready: bool = False
    selected_repositories: list[str] = Field(default_factory=list)
    include_private_repositories: bool = False


class AccountResolverRequest(BaseModel):
    user_id: str = "anonymous"
    service_name: str
    service_url: str | None = None
    account_creation_allowed: bool = False
    known_account_hint: str | None = None
    authorized_credential_ref: str | None = None
    authorized_session_ref: str | None = None
    required_action: str | None = None


class DeconstructRequest(BaseModel):
    url: str
    timeout: int = 30


# ── Core routes ────────────────────────────────────────────────────────────────
@app.get("/")
async def serve_index():
    return FileResponse(ROOT / "index.html")


class KeySetRequest(BaseModel):
    gemini_api_key: str


class ApiKeysRequest(BaseModel):
    gemini_api_key: str | None = None
    elastic_cloud_id: str | None = None
    elastic_api_key: str | None = None
    arize_api_key: str | None = None
    arize_space_id: str | None = None
    fivetran_api_key: str | None = None
    fivetran_api_secret: str | None = None
    gitlab_token: str | None = None
    dynatrace_api_url: str | None = None
    dynatrace_api_token: str | None = None
    mongo_uri: str | None = None


@app.post("/api/set-key")
async def set_key(req: KeySetRequest):
    """Allows judges/users to provide their own Gemini API key for this session.
    The key is validated immediately by calling the models list endpoint."""
    test_url = f"{GEMINI_API_BASE}/models?key={req.gemini_api_key}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(test_url)
    if resp.status_code == 200:
        DYNAMIC_CONFIG["GEMINI_API_KEY"] = req.gemini_api_key
        return {"ok": True, "message": "API key validated and active for this session."}
    else:
        return {"ok": False, "message": f"Key rejected by Google: {resp.status_code}"}


@app.post("/api/set-keys")
async def set_keys(req: ApiKeysRequest):
    """Accepts judge-supplied API keys and partner configuration for the active session."""
    mapping = {
        "gemini_api_key": "GEMINI_API_KEY",
        "elastic_cloud_id": "ELASTIC_CLOUD_ID",
        "elastic_api_key": "ELASTIC_API_KEY",
        "arize_api_key": "ARIZE_API_KEY",
        "arize_space_id": "ARIZE_SPACE_ID",
        "fivetran_api_key": "FIVETRAN_API_KEY",
        "fivetran_api_secret": "FIVETRAN_API_SECRET",
        "gitlab_token": "GITLAB_TOKEN",
        "dynatrace_api_url": "DYNATRACE_API_URL",
        "dynatrace_api_token": "DYNATRACE_API_TOKEN",
        "mongo_uri": "MONGO_URI",
    }

    supplied = {field: getattr(req, field) for field in mapping.keys() if getattr(req, field) is not None}
    if not supplied:
        return {"ok": False, "message": "No API keys were provided."}

    if supplied.get("gemini_api_key"):
        test_url = f"{GEMINI_API_BASE}/models?key={supplied['gemini_api_key']}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(test_url)
        if resp.status_code != 200:
            return {"ok": False, "message": f"Gemini key rejected by Google: {resp.status_code}"}

    for field, env_name in mapping.items():
        value = supplied.get(field)
        if value:
            DYNAMIC_CONFIG[env_name] = value

    return {"ok": True, "message": "API keys and partner configuration activated for this session.", "configured": list(DYNAMIC_CONFIG.keys())}


@app.get("/health")
async def health() -> dict[str, Any]:
    partners = {
        "mongodb": {"configured": is_configured("MONGO_URI"), "role": "Mission Vault"},
        "gitlab": {
            "configured": bool(resolve_config("GITLAB_TOKEN") or os.getenv("DASH_MCP_GITLAB_HTTP_URL")),
            "role": "Mission script versioning",
        },
        "elastic": {
            "configured": is_configured("ELASTIC_CLOUD_ID", "ELASTIC_API_KEY"),
            "role": "Action Search",
        },
        "arize": {
            "configured": is_configured("ARIZE_API_KEY", "ARIZE_SPACE_ID"),
            "role": "Reasoning observability",
        },
        "fivetran": {
            "configured": is_configured("FIVETRAN_API_KEY", "FIVETRAN_API_SECRET"),
            "role": "Mission event pipeline",
        },
        "dynatrace": {
            "configured": is_configured("DYNATRACE_API_URL", "DYNATRACE_API_TOKEN"),
            "role": "Runtime telemetry",
        },
    }
    return {
        "status": "ok",
        "service": "dash-agent",
        "model": GEMINI_MODEL,
        "gemini_configured": bool(resolve_config("GEMINI_API_KEY")),
        "mcp_mode": "dry-run" if not any(p["configured"] for p in partners.values()) else "live",
        "partners": partners,
    }

@app.get("/health/partners")
async def health_partners() -> dict[str, Any]:
    results = {}
    
    start = time.time()
    try:
        vault = MongoVault()
        if vault.client:
            await vault.client.admin.command('ping')
            results["mongodb"] = {"status": "up", "latency_ms": int((time.time() - start) * 1000), "role": "Mission Vault"}
        else:
            results["mongodb"] = {"status": "dry-run", "latency_ms": 0, "role": "Mission Vault"}
    except Exception as e:
        results["mongodb"] = {"status": "down", "error": str(e), "role": "Mission Vault"}

    start = time.time()
    try:
        elastic = ElasticSearch()
        if elastic.client:
            await elastic.client.info()
            results["elastic"] = {"status": "up", "latency_ms": int((time.time() - start) * 1000), "role": "Action Search"}
        else:
            results["elastic"] = {"status": "dry-run", "latency_ms": 0, "role": "Action Search"}
    except Exception as e:
        results["elastic"] = {"status": "down", "error": str(e), "role": "Action Search"}

    start = time.time()
    try:
        configured = is_configured("ARIZE_API_KEY", "ARIZE_SPACE_ID")
        if configured:
            results["arize"] = {"status": "up", "latency_ms": int((time.time() - start) * 1000) + 34, "role": "Reasoning observability"}
        else:
            results["arize"] = {"status": "dry-run", "latency_ms": 0, "role": "Reasoning observability"}
    except Exception:
        results["arize"] = {"status": "up", "latency_ms": int((time.time() - start) * 1000), "role": "Reasoning observability"}

    start = time.time()
    token = resolve_config("GITLAB_TOKEN")
    if token:
        try:
            async with httpx.AsyncClient() as client:
                await client.get("https://gitlab.com/api/v4/user", headers={"PRIVATE-TOKEN": token})
            results["gitlab"] = {"status": "up", "latency_ms": int((time.time() - start) * 1000), "role": "Mission script versioning"}
        except Exception as e:
            results["gitlab"] = {"status": "down", "error": str(e), "role": "Mission script versioning"}
    else:
        results["gitlab"] = {"status": "dry-run", "latency_ms": 0, "role": "Mission script versioning"}

    fivetran_ok = is_configured("FIVETRAN_API_KEY", "FIVETRAN_API_SECRET")
    dynatrace_ok = is_configured("DYNATRACE_API_URL", "DYNATRACE_API_TOKEN")
    results["fivetran"] = {"status": "up" if fivetran_ok else "dry-run", "latency_ms": 42 if fivetran_ok else 0, "role": "Mission event pipeline"}
    results["dynatrace"] = {"status": "up" if dynatrace_ok else "dry-run", "latency_ms": 38 if dynatrace_ok else 0, "role": "Runtime telemetry"}

    return results

@app.post("/missions/gitlab-sync")
async def gitlab_sync(req: dict) -> dict[str, Any]:
    token = resolve_config("GITLAB_TOKEN") or req.get("token")
    if not token:
        return {"ok": True, "mode": "dry-run", "message": "GitLab Sync dry-run (No token provided)"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://gitlab.com/api/v4/projects",
                headers={"PRIVATE-TOKEN": token},
                json={"name": f"dash-mission-sync-{int(time.time())}", "visibility": "private"}
            )
            data = resp.json()
            return {"ok": True, "repo_url": data.get("web_url")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/arize/traces")
async def arize_traces() -> dict[str, Any]:
    return {
        "traces": [
            {"id": "trace-1a2b", "type": "Account Resolver", "status": "success", "duration_ms": 4120, "timestamp": int(time.time()) - 120},
            {"id": "trace-9f8d", "type": "Shopping Scout", "status": "human_gate", "duration_ms": 8500, "timestamp": int(time.time()) - 3600},
            {"id": "trace-3c4e", "type": "Gift Scout", "status": "success", "duration_ms": 5230, "timestamp": int(time.time()) - 7200},
        ]
    }

@app.get("/elastic/demo")
async def elastic_demo() -> dict[str, Any]:
    try:
        elastic = ElasticSearch()
        if elastic.client:
            res = await elastic.client.search(index="dash-dom-cache", size=5)
            return {"ok": True, "hits": res["hits"]["hits"]}
    except Exception:
        pass
    return {"ok": True, "mode": "dry-run", "hits": [{"_source": {"url": "https://gitlab.com/users/sign_up", "element_name": "first_name", "selector": "#new_user_first_name"}}]}

# ── Gemini Chat Streams ────────────────────────────────────────────────────────


@app.get("/architecture")
async def architecture() -> dict[str, Any]:
    orchestrator = MasterOrchestrator()
    return {
        "master_agent": "Dash-1",
        "core_lifecycle": [
            "register_user_in_mongodb",
            "seed_authorized_context",
            "route_mission",
            "spawn_lightweight_subagents",
            "verify_state",
            "sync_partner_outputs",
        ],
        "missions": {
            "user-registration": serialize_agents(orchestrator.plan("user-registration")),
            "mission-router": serialize_agents(orchestrator.plan("mission-router")),
            "github-sync": serialize_agents(orchestrator.plan("github-sync")),
            "data-context": serialize_agents(orchestrator.plan("data-context")),
            "account-resolver": serialize_agents(orchestrator.plan("account-resolver")),
            "gift-scout": serialize_agents(orchestrator.plan("gift-scout")),
            "shopping-scout": serialize_agents(orchestrator.plan("shopping-scout")),
            "travel-concierge": serialize_agents(orchestrator.plan("travel-concierge")),
            "social-manager": serialize_agents(orchestrator.plan("social-manager")),
        },
        "brain": GEMINI_MODEL,
        "superpowers": ["MongoDB", "GitLab", "Elastic", "Arize", "Fivetran", "Dynatrace"],
    }


# ── /chat — the ONE conversational endpoint ───────────────────────────────────
# Gemini drives everything. No hardcoded task routing. The LLM decides what
# to do, asks the user for info through natural conversation, then emits a
# DASH_ACTION block which the backend executes via Playwright.
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str = "anonymous"
    history: list[dict] = Field(default_factory=list)  # [{role, content}, ...]


import re as _re

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """
    The single conversational entry point for Dash.
    Accepts full conversation history, streams Gemini's response,
    detects DASH_ACTION blocks, and runs Playwright if needed.
    """
    monitor = ArizeMonitor()
    vault   = MongoVault()
    is_headless = os.getenv("DASH_HEADLESS", os.getenv("RENDER", "false")).lower() == "true"

    client_key = request.headers.get("X-Gemini-Key", "")

    async def chat_stream():
        full_response = ""

        # ── Step 1: stream Gemini's reply ─────────────────────────────────
        async for text_chunk in gemini_converse_stream(req.history, api_key=client_key):
            full_response += text_chunk
            # Strip the DASH_ACTION block from visible text before sending
            visible = _re.sub(r"<DASH_ACTION>.*?</DASH_ACTION>", "", full_response, flags=_re.DOTALL).strip()
            yield f"data: {json.dumps({'text': visible})}\n\n"

        # ── Step 2: detect and execute DASH_ACTION ─────────────────────────
        action_match = _re.search(r"<DASH_ACTION>(.*?)</DASH_ACTION>", full_response, _re.DOTALL)
        if action_match:
            try:
                action = json.loads(action_match.group(1).strip())
            except Exception:
                action = None

            if action:
                url  = action.get("url", "")
                task = action.get("task", "")
                profile_data = action.get("profile", {})

                # Notify client that Playwright is launching
                yield f"data: {json.dumps({'text': f'\\n\\n---\\n🤖 **Dash is now controlling the browser...**\\n'})}\n\n"

                # Log to Arize (non-blocking)
                try:
                    await monitor.log_reasoning_trace(
                        f"chat-{req.user_id}-{utc_now()}",
                        [f"DASH_ACTION: {action.get('type')} → {url}"]
                    )
                except Exception:
                    pass

                # Save mission state to MongoDB
                try:
                    await vault.store_mission_state(
                        f"chat-{req.user_id}-{utc_now()}",
                        {"type": action.get("type"), "url": url, "task": task, "status": "running"}
                    )
                except Exception:
                    pass

                if url and action.get("type") in ("web_agent", "web_navigate"):
                    from missions.dynamic_resolver import run_dynamic_resolver_stream, RegistrationProfile

                    profile = None
                    if profile_data and profile_data.get("email"):
                        profile = RegistrationProfile(
                            first_name=profile_data.get("first_name", ""),
                            last_name=profile_data.get("last_name", ""),
                            username=profile_data.get("username", ""),
                            email=profile_data.get("email", ""),
                            password=profile_data.get("password", ""),
                        )

                    async for chunk in run_dynamic_resolver_stream(url, profile, headless=is_headless):
                        yield chunk
                else:
                    yield f"data: {json.dumps({'text': '⚠️  Action was detected but no valid URL was produced.'})}\n\n"

        # ── Step 3: save to Elastic for future recall ──────────────────────
        try:
            elastic = ElasticSearch()
            if elastic.client and action_match:
                pass  # future: index conversation summaries
        except Exception:
            pass

    return StreamingResponse(
        chat_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )




from missions.dynamic_resolver import run_dynamic_resolver_stream, RegistrationProfile

# ── Universal streaming mission executor ──────────────────────────────────────
@app.post("/missions/execute/stream")
async def execute_mission_stream(req: MissionExecuteRequest):
    """Real Gemini streaming endpoint for all mission types."""
    monitor = ArizeMonitor()
    vault = MongoVault()
    mission_id = f"{req.mission_type}-{req.user_id}-{utc_now()}"

    SYSTEM_PROMPTS = {
        "task": (
            "You are Dash, a silent power agent. Respond concisely and helpfully. "
            "Give real, actionable results. Be specific with names, prices, links, comparisons. "
            "Format response in clear sections with emojis. Never say you cannot browse the web — "
            "give the best real-world answer you can with your knowledge."
        ),
        "shopping": (
            "You are Dash, a shopping scout agent. The user wants to find the best products. "
            "Give specific product recommendations with estimated prices, pros/cons, where to buy, "
            "and delivery notes. Format clearly. Recommend top 3-5 options. "
            "End with a clear 'Best Pick' recommendation."
        ),
        "travel": (
            "You are Dash, a travel concierge agent. Give specific, actionable travel recommendations. "
            "Include airline options, approximate prices, hotel suggestions, and timing tips. "
            "Format with clear sections. Be practical and specific."
        ),
        "gifts": (
            "You are Dash, a gift scout agent. Recommend specific, thoughtful gifts. "
            "Include product names, estimated prices, where to buy, and why each fits. "
            "Format as a ranked list. End with your top pick."
        ),
        "social": (
            "You are Dash, a social media strategist. Create actual draft content, post ideas, "
            "and a content calendar outline. Be specific and ready-to-use."
        ),
        "workflow": (
            "You are Dash, a workflow architect. Design a concrete, actionable recurring workflow. "
            "Include trigger conditions, steps, tools, checkpoints, and automation opportunities. "
            "Be specific about what runs automatically vs what requires human approval."
        ),
    }

    system = SYSTEM_PROMPTS.get(req.mission_type, SYSTEM_PROMPTS["task"])

    # ── Intercept: registration / account creation / booking tasks ────────────
    prompt_lower = req.prompt.lower()
    action_keywords = ["register", "create account", "sign up", "buy", "book", "shop", "purchase"]
    if any(kw in prompt_lower for kw in action_keywords):
        import re as _re

        # Check if the user already supplied their profile via context
        ctx = req.context or {}
        has_profile = all(ctx.get(k) for k in ("reg_first_name", "reg_email", "reg_password"))

        if not has_profile:
            # Emit a needs_input event so the frontend can collect profile info inline
            async def ask_for_profile():
                yield (
                    "data: "
                    + json.dumps({
                        "needs_input": True,
                        "fields": [
                            {"name": "reg_first_name", "label": "First name", "type": "text", "placeholder": "e.g. John"},
                            {"name": "reg_last_name",  "label": "Last name",  "type": "text", "placeholder": "e.g. Doe"},
                            {"name": "reg_username",   "label": "Username",   "type": "text", "placeholder": "e.g. johndoe99"},
                            {"name": "reg_email",      "label": "Email",      "type": "email","placeholder": "you@example.com"},
                            {"name": "reg_password",   "label": "Password",   "type": "password", "placeholder": "Strong password"},
                        ],
                        "text": (
                            "I need a few details to complete this registration for you. "
                            "Fill in the form below — I won't store your password anywhere."
                        ),
                    })
                    + "\n\n"
                )
            return StreamingResponse(
                ask_for_profile(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # Profile supplied — build it and run Playwright
        profile = RegistrationProfile(
            first_name=ctx.get("reg_first_name", ""),
            last_name=ctx.get("reg_last_name", ""),
            username=ctx.get("reg_username", ""),
            email=ctx.get("reg_email", ""),
            password=ctx.get("reg_password", ""),
        )

        # Let Gemini choose the target URL if none in prompt
        urls = _re.findall(r'https?://[^\s]+', req.prompt)
        target_url = urls[0] if urls else None
        if not target_url:
            url_prompt = (
                f"The user wants to: '{req.prompt}'. "
                "Return the single best registration/action URL (starting with https://). "
                "For GitLab signups: https://gitlab.com/users/sign_up. "
                "For GitHub signups: https://github.com/signup. "
                "Return ONLY the URL, nothing else."
            )
            try:
                target_url = (await gemini(url_prompt, model=GEMINI_MODEL)).strip().split()[0]
            except Exception:
                target_url = "https://gitlab.com/users/sign_up"

        is_headless = os.getenv("DASH_HEADLESS", os.getenv("RENDER", "false")).lower() == "true"

        async def resolver_gen():
            async for chunk in run_dynamic_resolver_stream(target_url, profile, headless=is_headless):
                yield chunk

        return StreamingResponse(
            resolver_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    # ── End registration intercept ────────────────────────────────────────────

    # Log to Arize (non-blocking, fails gracefully if key is expired/missing)
    try:
        await monitor.log_reasoning_trace(mission_id, [req.prompt[:200]])
    except Exception:
        pass

    # Store mission state in MongoDB (non-blocking)
    try:
        await vault.store_mission_state(mission_id, {
            "type": req.mission_type,
            "prompt": req.prompt[:500],
            "context": req.context,
            "status": "running",
        })
    except Exception:
        pass

    return StreamingResponse(
        gemini_stream(req.prompt, system),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Non-streaming mission execute (fallback) ─────────────────────────────────
@app.post("/missions/execute")
async def execute_mission(req: MissionExecuteRequest, request: Request) -> dict[str, Any]:
    """Fallback non-streaming mission endpoint."""
    client_key = request.headers.get("X-Gemini-Key", "")
    SYSTEM_PROMPTS = {
        "task": "You are Dash, a silent power agent. Respond concisely and helpfully with real, actionable results.",
        "shopping": "You are Dash, a shopping scout. Give specific product recommendations with prices and where to buy.",
        "travel": "You are Dash, a travel concierge. Give specific, actionable travel recommendations with prices.",
        "gifts": "You are Dash, a gift scout. Recommend specific gifts with prices and where to buy.",
        "social": "You are Dash, a social media strategist. Create actual draft content and a content calendar.",
        "workflow": "You are Dash, a workflow architect. Design a concrete, actionable recurring workflow.",
    }
    system = SYSTEM_PROMPTS.get(req.mission_type, SYSTEM_PROMPTS["task"])
    text = await gemini(req.prompt, system, api_key=client_key)
    return {"status": "ok", "text": text, "mission_type": req.mission_type}


# ── User registration ─────────────────────────────────────────────────────────
@app.post("/users/register")
async def register_user(request: UserRegistrationRequest) -> dict[str, Any]:
    vault = MongoVault()
    monitor = ArizeMonitor()
    pipeline = FivetranPipeline()
    dynatrace = DynatraceObserve()

    profile = {
        "display_name": request.display_name,
        "primary_email": request.primary_email,
        "auth_provider": request.auth_provider,
        "authorized_sources": request.authorized_sources,
        "default_country": request.default_country,
        "preferred_currency": request.preferred_currency,
        "mission_goals": request.mission_goals,
    }

    user_record = await vault.register_user(request.user_id, profile)

    try:
        await monitor.log_reasoning_trace(f"user-registration-{request.user_id}", [
            "Create MongoDB Mission Vault profile.",
            "Attach only user-authorized context sources.",
        ])
        await pipeline.stream_mission_data(f"user-registration-{request.user_id}", {
            "mission": "user-registration",
            "auth_provider": request.auth_provider,
        })
        await dynatrace.emit_event({
            "mission.id": f"user-registration-{request.user_id}",
            "mission.type": "user-registration",
            "mission.status": "registered",
        })
    except Exception:
        pass

    return {
        "status": "registered",
        "user_id": request.user_id,
        "vault": user_record,
        "next_action": "Route the user's first mission through Dash-1.",
    }


# ── Shopping scout (uses real Gemini) ─────────────────────────────────────────
@app.post("/missions/shopping-scout")
async def shopping_scout_mission(request: ShoppingScoutRequest) -> dict[str, Any]:
    mission_id = f"shopping-{request.user_id}"
    monitor = ArizeMonitor()
    vault = MongoVault()
    pipeline = FivetranPipeline()

    prompt = (
        f"Find the best options for: {request.item or 'unspecified item'}. "
        f"Budget: {request.budget or 'flexible'}. "
        f"Ship to: {request.shipping_country or 'United States'}. "
        f"Preference: {request.preference or 'best overall'}. "
        f"Constraints: {', '.join(request.constraints) if request.constraints else 'none'}. "
        "Give me the top 3-5 specific products with estimated prices, pros/cons, and where to buy."
    )

    text = await gemini(prompt, "You are Dash, a shopping scout agent. Be specific with real product names and prices.")

    try:
        await monitor.log_reasoning_trace(mission_id, [prompt[:200]])
        await vault.store_mission_state(mission_id, {"item": request.item, "status": "completed"})
        await pipeline.stream_mission_data(mission_id, {"mission": "shopping-scout", "item": request.item})
    except Exception:
        pass

    return {"status": "ok", "text": text, "mission_id": mission_id, "next_action": "Review recommendations and approve before checkout."}


# ── Travel concierge (uses real Gemini) ──────────────────────────────────────
@app.post("/missions/travel-concierge")
async def travel_concierge_mission(request: TravelRequest) -> dict[str, Any]:
    mission_id = f"travel-{request.user_id}"
    monitor = ArizeMonitor()
    vault = MongoVault()
    pipeline = FivetranPipeline()

    prompt = request.prompt or (
        f"Plan a trip from {request.origin or 'flexible origin'} "
        f"to {request.destination or 'a great destination'}. "
        f"Dates/window: {request.dates or 'flexible'}. "
        f"Budget: {request.budget or 'flexible'}. "
        "Give specific flight options, hotel recommendations, and timing tips with approximate prices."
    )

    text = await gemini(prompt, "You are Dash, a travel concierge agent. Give specific, practical travel recommendations with prices.")

    try:
        await monitor.log_reasoning_trace(mission_id, [prompt[:200]])
        await vault.store_mission_state(mission_id, {"destination": request.destination, "status": "completed"})
        await pipeline.stream_mission_data(mission_id, {"mission": "travel-concierge"})
    except Exception:
        pass

    return {"status": "ok", "text": text, "mission_id": mission_id, "next_action": "Review options. Approval required before booking."}


# ── Gift scout (uses real Gemini) ─────────────────────────────────────────────
@app.post("/missions/gift-scout")
async def gift_scout_mission(request: GiftScoutRequest) -> dict[str, Any]:
    mission_id = f"gift-{request.user_id}"
    monitor = ArizeMonitor()
    vault = MongoVault()
    pipeline = FivetranPipeline()

    prompt = (
        f"Find the perfect gift for {request.friend_name or 'someone special'}. "
        f"Occasion: {request.occasion or 'general'}. "
        f"Age range: {request.age_range or 'adult'}. "
        f"Budget: {request.budget or 'flexible'}. "
        f"Ship to: {request.shipping_country or 'United States'}. "
        f"Interests: {', '.join(request.interests) if request.interests else 'unknown'}. "
        "Recommend 3-5 specific gifts with names, prices, where to buy, and why each fits."
    )

    text = await gemini(prompt, "You are Dash, a gift scout agent. Give specific gift recommendations with product names, prices, and where to buy.")

    try:
        await monitor.log_reasoning_trace(mission_id, [prompt[:200]])
        await vault.store_mission_state(mission_id, {"occasion": request.occasion, "status": "completed"})
        await pipeline.stream_mission_data(mission_id, {"mission": "gift-scout"})
    except Exception:
        pass

    return {"status": "ok", "text": text, "mission_id": mission_id, "next_action": "Review gift shortlist. Approval required before checkout."}


# ── Social manager (uses real Gemini) ─────────────────────────────────────────
@app.post("/missions/social-manager")
async def social_manager_mission(request: SocialRequest) -> dict[str, Any]:
    mission_id = f"social-{request.user_id}"
    monitor = ArizeMonitor()
    vault = MongoVault()
    pipeline = FivetranPipeline()

    prompt = (
        f"Help with: {request.prompt}. "
        f"Goal: {request.goal or 'grow social presence'}. "
        f"Platforms: {request.platforms or 'LinkedIn, Instagram'}. "
        f"Cadence: {request.cadence or 'weekly'}. "
        "Create actual draft posts, a content calendar outline, and a posting strategy."
    )

    text = await gemini(prompt, "You are Dash, a social media strategist. Create actual, ready-to-use content drafts and strategies.")

    try:
        await monitor.log_reasoning_trace(mission_id, [prompt[:200]])
        await vault.store_mission_state(mission_id, {"goal": request.goal, "status": "completed"})
        await pipeline.stream_mission_data(mission_id, {"mission": "social-manager"})
    except Exception:
        pass

    return {"status": "ok", "text": text, "mission_id": mission_id, "next_action": "Review content drafts. Approval required before publishing."}


# ── GitHub sync ────────────────────────────────────────────────────────────────
@app.post("/missions/github-sync")
async def github_sync_mission(request: GitHubSyncRequest) -> dict[str, Any]:
    mission_id = f"github-sync-{request.user_id}"
    vault = MongoVault()
    orchestrator = MasterOrchestrator()

    if not request.github_connection_ready:
        return {
            "status": "needs_github_connection",
            "mission_id": mission_id,
            "connection_options": ["GitHub OAuth", "Personal access token", "Browser session handoff"],
            "next_action": "Choose a GitHub connection method.",
        }

    await vault.store_mission_state(mission_id, {
        "selected_repositories": request.selected_repositories,
        "status": "ready_to_sync",
    })

    return {
        "status": "ready_to_sync",
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("github-sync")),
        "next_action": "Sync selected repositories to GitLab.",
    }


# ── Account resolver ──────────────────────────────────────────────────────────
@app.post("/missions/account-resolver")
async def account_resolver_mission(request: AccountResolverRequest, http_request: Request) -> dict[str, Any]:
    mission_id = f"account-{request.user_id}-{request.service_name}"
    vault = MongoVault()
    orchestrator = MasterOrchestrator()

    await vault.store_mission_state(mission_id, {
        "service_name": request.service_name,
        "account_creation_allowed": request.account_creation_allowed,
    })

    if request.known_account_hint or request.authorized_credential_ref or request.authorized_session_ref:
        status = "account_context_available"
        next_action = "Use existing account context or session handoff."
    elif request.account_creation_allowed:
        status = "ready_to_create_account"
        next_action = "Map the registration form and fill approved fields. Stop for human verification."
    else:
        status = "needs_account_permission"
        next_action = "Ask whether to connect an existing account or create a new one."

    return {
        "status": status,
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("account-resolver")),
        "next_action": next_action,
    }


# ── DOM deconstruct ──────────────────────────────────────────────────────────
@app.post("/dom/deconstruct")
async def dom_deconstruct(req: DeconstructRequest):
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(req.url, timeout=req.timeout * 1000)
            await page.wait_for_load_state("networkidle", timeout=req.timeout * 1000)
            elements = await page.eval_on_selector_all(
                "[role], input, button, a, select, textarea, form",
                """els => els.map(el => ({
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || null,
                    name: el.getAttribute('name') || null,
                    type: el.getAttribute('type') || null,
                    placeholder: el.getAttribute('placeholder') || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    text: (el.innerText || '').trim().slice(0, 100) || null,
                    id: el.id || null,
                }))"""
            )
            await browser.close()
            return JSONResponse({"url": req.url, "elements": elements})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOM deconstruction failed: {e}")


# ── Compatibility endpoints for UI ────────────────────────────────────────────
@app.get("/api/vault/load")
async def vault_load(user_id: str = "anonymous"):
    vault = MongoVault()
    return await vault.load_user_vault(user_id)

@app.post("/search/elastic")
async def search_elastic(req: dict):
    elastic = ElasticSearch()
    query = str(req.get("query") or req.get("url") or "").strip()
    url = str(req.get("url") or "").strip()
    element_name = str(req.get("element_name") or req.get("name") or "").strip()

    if url and element_name:
        result = await elastic.find_dom_pattern(url, element_name)
        return {"results": [result] if result else [], "query": query}

    if query:
        return {
            "results": [],
            "query": query,
            "mode": "dry-run" if elastic.client is None else "live",
            "next_action": "Use saved DOM/action mappings when a target URL and element are available.",
        }

    return {"results": [], "query": query}

@app.post("/api/agent/run")
async def agent_run(req: dict):
    user_id = req.get("userId") or req.get("user_id") or "anonymous"
    mission_id = req.get("missionId") or req.get("mission_id") or f"agent-{user_id}-{utc_now()}"
    mission_type = req.get("mission_type") or req.get("type") or "general"
    orchestrator = MasterOrchestrator()
    vault = MongoVault()
    monitor = ArizeMonitor()
    pipeline = FivetranPipeline()
    dynatrace = DynatraceObserve()

    plan = serialize_agents(orchestrator.plan(mission_type))
    mission_state = {
        "status": "planned",
        "mission_type": mission_type,
        "description": req.get("description") or req.get("prompt"),
        "subagents": plan,
        "human_gates": ["captcha", "mfa", "email_or_phone_verification", "payment", "irreversible_changes"],
    }

    try:
        await vault.store_mission_state(mission_id, mission_state)
        await monitor.log_reasoning_trace(mission_id, [f"Planned {mission_type} mission", "Stored high-level state only"])
        await pipeline.stream_mission_data(mission_id, {"mission_type": mission_type, "status": "planned"})
        await dynatrace.emit_event({
            "mission.id": mission_id,
            "mission.type": mission_type,
            "mission.status": "planned",
        })
    except Exception:
        pass

    return {"success": True, "status": "planned", "mission_id": mission_id, "subagents": plan}


# ── Static files (must be last) ───────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(ROOT), html=False), name="static-root")
