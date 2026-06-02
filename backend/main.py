import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from superpowers.arize_monitor import ArizeMonitor
from superpowers.elastic_search import ElasticSearch
from superpowers.fivetran_pipeline import FivetranPipeline
from superpowers.mongo_vault import MongoVault
from backend.orchestrator import MasterOrchestrator, serialize_agents
from backend.auth import router as auth_router

ROOT = Path(__file__).resolve().parents[1]

# ── Env vars ────────────────────────────────────────────────────────────────
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL    = "gemini-2.0-flash"

app = FastAPI(title="Dash Agent Mission Orchestrator")
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
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


# ── Helpers ──────────────────────────────────────────────────────────────────
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def gemini(prompt: str, system: str = "", model: str = GEMINI_MODEL) -> str:
    """Call Gemini with the server API key. Raises HTTPException if not configured."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured on the server.")

    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
    }
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={GEMINI_API_KEY}"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def gemini_stream(prompt: str, system: str = "", model: str = GEMINI_MODEL):
    """Generator that yields Server-Sent Event chunks from Gemini streaming API."""
    if not GEMINI_API_KEY:
        yield f"data: {json.dumps({'error': 'GEMINI_API_KEY not configured'})}\n\n"
        return

    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
    }
    url = f"{GEMINI_API_BASE}/models/{model}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"

    async with httpx.AsyncClient(timeout=120) as client:
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "dash-agent", "gemini_configured": bool(GEMINI_API_KEY)}


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
        },
        "brain": "Gemini 2.0 Flash",
        "superpowers": ["MongoDB", "Elastic", "Arize", "Fivetran"],
    }


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

    # Intercept Universal Dynamic Account Resolver
    prompt_lower = req.prompt.lower()
    if any(keyword in prompt_lower for keyword in ["register", "create account", "buy", "book", "shop", "purchase"]):
        # Quick heuristic to extract URL or fallback to guessing based on service name
        import re
        urls = re.findall(r'https?://[^\s]+', req.prompt)
        target_url = urls[0] if urls else None
        
        if not target_url:
            if "gitlab" in prompt_lower: target_url = "https://gitlab.com/users/sign_up"
            elif "github" in prompt_lower: target_url = "https://github.com/signup"
            elif "linkedin" in prompt_lower: target_url = "https://www.linkedin.com/signup"
            elif "amazon" in prompt_lower or "buy" in prompt_lower or "shop" in prompt_lower or "purchase" in prompt_lower: target_url = "https://www.amazon.com"
            elif "expedia" in prompt_lower or "book" in prompt_lower: target_url = "https://www.expedia.com"
            else: target_url = "https://example.com/signup"

        async def dynamic_resolver_generator():
            profiles = await vault.get_registration_profile(req.user_id)
            if profiles and len(profiles) > 0:
                p = profiles[0]
                profile = RegistrationProfile(
                    first_name=p.get("first_name", "Dash"),
                    last_name=p.get("last_name", "Agent"),
                    username=p.get("username", f"dash-agent-{req.user_id}"),
                    email=p.get("email", f"dash-{req.user_id}@example.com"),
                    password="DashSecurePassword123!"
                )
            else:
                profile = RegistrationProfile(
                    first_name="Dash",
                    last_name="Agent",
                    username="dash-agent-demo-001",
                    email="dash-demo@example.com",
                    password="DashSecurePassword123!"
                )
            
            is_headless = os.getenv("RENDER", "false").lower() == "true"
            async for chunk in run_dynamic_resolver_stream(target_url, profile, headless=is_headless):
                yield chunk
                
        return StreamingResponse(
            dynamic_resolver_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Log to Arize (non-blocking)
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
async def execute_mission(req: MissionExecuteRequest) -> dict[str, Any]:
    """Fallback non-streaming mission endpoint."""
    SYSTEM_PROMPTS = {
        "task": "You are Dash, a silent power agent. Respond concisely and helpfully with real, actionable results.",
        "shopping": "You are Dash, a shopping scout. Give specific product recommendations with prices and where to buy.",
        "travel": "You are Dash, a travel concierge. Give specific, actionable travel recommendations with prices.",
        "gifts": "You are Dash, a gift scout. Recommend specific gifts with prices and where to buy.",
        "social": "You are Dash, a social media strategist. Create actual draft content and a content calendar.",
        "workflow": "You are Dash, a workflow architect. Design a concrete, actionable recurring workflow.",
    }
    system = SYSTEM_PROMPTS.get(req.mission_type, SYSTEM_PROMPTS["task"])
    text = await gemini(req.prompt, system)
    return {"status": "ok", "text": text, "mission_type": req.mission_type}


# ── User registration ─────────────────────────────────────────────────────────
@app.post("/users/register")
async def register_user(request: UserRegistrationRequest) -> dict[str, Any]:
    vault = MongoVault()
    monitor = ArizeMonitor()
    pipeline = FivetranPipeline()

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
async def account_resolver_mission(request: AccountResolverRequest) -> dict[str, Any]:
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
async def vault_load():
    return {"user": {}, "memory": {}}

@app.post("/search/elastic")
async def search_elastic(req: dict):
    return {"results": []}

@app.post("/api/agent/run")
async def agent_run(req: dict):
    return {"success": True, "status": "completed"}


# ── Static files (must be last) ───────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(ROOT), html=False), name="static-root")
