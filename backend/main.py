from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from superpowers.arize_monitor import ArizeMonitor
from superpowers.elastic_search import ElasticSearch
from superpowers.fivetran_pipeline import FivetranPipeline
from superpowers.gitlab_sync import GitLabSync
from superpowers.mongo_vault import MongoVault
from backend.orchestrator import MasterOrchestrator, serialize_agents


ROOT = Path(__file__).resolve().parents[1]
MISSION_SCRIPT = ROOT / "missions" / "gitlab_registration.py"

app = FastAPI(title="Dash Agent Mission Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# OWASP Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000;"
    return response


@app.get("/")
async def serve_index():
    return FileResponse(ROOT / "index.html")


app.mount("/", StaticFiles(directory=str(ROOT), html=False), name="static-root")


class MissionRequest(BaseModel):
    user_id: str = "demo-user"
    query: str = "Register my GitLab account and provision my mission repo."
    verification_completed: bool = False


class UserRegistrationRequest(BaseModel):
    user_id: str = "demo-user"
    display_name: str | None = None
    primary_email: str | None = None
    auth_provider: str = "email"
    authorized_sources: list[str] = Field(default_factory=list)
    default_country: str | None = None
    preferred_currency: str | None = None
    mission_goals: list[str] = Field(default_factory=list)


class GiftScoutRequest(BaseModel):
    user_id: str = "demo-user"
    friend_name: str | None = None
    occasion: str | None = None
    budget: str | None = None
    relationship: str | None = None
    age_range: str | None = None
    interests: list[str] = Field(default_factory=list)
    public_social_links: list[str] = Field(default_factory=list)
    connected_social_session: bool = False
    shipping_country: str | None = None


class GitHubSyncRequest(BaseModel):
    user_id: str = "demo-user"
    github_connection_ready: bool = False
    selected_repositories: list[str] = Field(default_factory=list)
    include_private_repositories: bool = False


class DataContextRequest(BaseModel):
    user_id: str = "demo-user"
    allowed_sources: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] = Field(default_factory=list)
    context_expiry_days: int = 30


class AccountResolverRequest(BaseModel):
    user_id: str = "demo-user"
    service_name: str
    service_url: str | None = None
    account_creation_allowed: bool = False
    known_account_hint: str | None = None
    authorized_credential_ref: str | None = None
    authorized_session_ref: str | None = None
    required_action: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def phase(name: str, status: str, detail: str) -> dict[str, str]:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "timestamp": utc_now(),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "dash-agent"}


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
        },
        "brain": "Google Cloud Agent Builder (Gemini 3)",
        "superpowers": ["MongoDB", "Elastic", "Arize", "Fivetran"],
    }


@app.post("/users/register")
async def register_user(request: UserRegistrationRequest) -> dict[str, Any]:
    user_id = request.user_id
    orchestrator = MasterOrchestrator()
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

    user_record = await vault.register_user(user_id, profile)
    context_records = [
        await vault.store_context_source(user_id, {
            "provider": source,
            "scope": "user-approved-context",
            "status": "authorized_reference_pending" if source in {"google", "apple", "github"} else "available",
        })
        for source in request.authorized_sources
    ]

    await monitor.log_reasoning_trace(
        f"user-registration-{user_id}",
        [
            "Create the MongoDB Mission Vault profile first.",
            "Attach only user-authorized context sources.",
            "Route future requests to lightweight mission sub-agents.",
            "Keep raw account passwords and tokens out of logs and chat.",
        ],
    )
    await pipeline.stream_mission_data(f"user-registration-{user_id}", {
        "mission": "user-registration",
        "auth_provider": request.auth_provider,
        "authorized_source_count": len(request.authorized_sources),
        "mission_goal_count": len(request.mission_goals),
    })

    return {
        "status": "registered",
        "user_id": user_id,
        "vault": user_record,
        "context_sources": context_records,
        "subagents": serialize_agents(orchestrator.plan("user-registration")),
        "next_action": "Route the user's first mission through Dash-1.",
    }


@app.post("/execute-mission")
async def execute_mission(request: MissionRequest) -> dict[str, Any]:
    # Default to a generic reasoning mission using Google AI Builder
    return {
        "status": "success",
        "mission_id": f"mission-{request.user_id}",
        "brain": "Google Cloud Agent Builder",
        "summary": f"Analyzing mission: {request.query}",
        "next_action": "Spawning relevant sub-agents for the requested task."
    }


@app.post("/missions/gift-scout")
async def gift_scout_mission(request: GiftScoutRequest) -> dict[str, Any]:
    """
    Consumer mission: choose a high-fit gift at the best practical price.

    Dash never stores raw Instagram/Facebook credentials. It can use public
    links, user exports, OAuth/session handoff, or a fallback questionnaire.
    """
    mission_id = f"gift-scout-{request.user_id}"
    orchestrator = MasterOrchestrator()
    vault = MongoVault()
    monitor = ArizeMonitor()
    search = ElasticSearch()
    pipeline = FivetranPipeline()

    allowed_social_context = bool(request.public_social_links or request.connected_social_session)
    missing_questions = []
    if not allowed_social_context and not request.age_range:
        missing_questions.append("What is your friend's age range?")
    if not allowed_social_context and not request.interests:
        missing_questions.append("What hobbies, fandoms, brands, or styles do they like?")
    if not request.budget:
        missing_questions.append("What budget should I stay under?")
    if not request.occasion:
        missing_questions.append("What is the occasion?")
    if not request.shipping_country:
        missing_questions.append("Where does the gift need to ship?")

    await monitor.log_reasoning_trace(
        mission_id,
        [
            "Start with consented friend context.",
            "Prefer public links, exports, or browser session handoff over raw social credentials.",
            "Fallback to age, relationship, occasion, budget, interests, and shipping country.",
            "Rank candidates by fit confidence, price, delivery confidence, and seller reliability.",
            "Stop before checkout for explicit user confirmation.",
        ],
    )

    await vault.store_mission_state(mission_id, {
        "friend_name": request.friend_name,
        "occasion": request.occasion,
        "budget": request.budget,
        "relationship": request.relationship,
        "age_range": request.age_range,
        "interests": request.interests,
        "public_social_links_count": len(request.public_social_links),
        "connected_social_session": request.connected_social_session,
        "shipping_country": request.shipping_country,
    })

    product_pattern = await search.find_dom_pattern("shopping", "product_card_price_shipping")
    await pipeline.stream_mission_data(mission_id, {
        "mission": "gift-scout",
        "status": "needs_context" if missing_questions else "ready_to_recommend",
        "allowed_social_context": allowed_social_context,
        "missing_question_count": len(missing_questions),
    })

    if missing_questions:
        return {
            "status": "needs_context",
            "mission_id": mission_id,
            "subagents": serialize_agents(orchestrator.plan("gift-scout")),
            "allowed_context": {
                "public_social_links": request.public_social_links,
                "connected_social_session": request.connected_social_session,
                "raw_social_passwords_stored": False,
            },
            "questions": missing_questions,
        }

    return {
        "status": "ready_to_recommend",
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("gift-scout")),
        "ranking_model": {
            "fit_confidence": "interest overlap, relationship, occasion, novelty",
            "price_score": "total landed cost against budget",
            "delivery_confidence": "shipping speed, destination, seller reliability",
            "risk_flags": "fragile, sizing uncertainty, low seller trust, late delivery",
        },
        "next_action": "Search candidate products, rank top options, and ask for approval before checkout.",
        "product_pattern": product_pattern,
    }


@app.post("/missions/github-sync")
async def github_sync_mission(request: GitHubSyncRequest) -> dict[str, Any]:
    mission_id = f"github-sync-{request.user_id}"
    orchestrator = MasterOrchestrator()
    vault = MongoVault()
    monitor = ArizeMonitor()
    pipeline = FivetranPipeline()

    await monitor.log_reasoning_trace(
        mission_id,
        [
            "Do not ask for a GitHub password.",
            "Offer OAuth, a vault-stored token, or browser session handoff.",
            "List only repositories the user authorizes.",
            "Ask before importing or mirroring into GitLab.",
        ],
    )
    await vault.store_mission_state(mission_id, {
        "github_connection_ready": request.github_connection_ready,
        "selected_repositories": request.selected_repositories,
        "include_private_repositories": request.include_private_repositories,
    })
    await pipeline.stream_mission_data(mission_id, {
        "mission": "github-sync",
        "github_connection_ready": request.github_connection_ready,
        "selected_repository_count": len(request.selected_repositories),
    })

    if not request.github_connection_ready:
        return {
            "status": "needs_github_connection",
            "mission_id": mission_id,
            "subagents": serialize_agents(orchestrator.plan("github-sync")),
            "connection_options": [
                "GitHub OAuth",
                "Personal access token stored in the Mission Vault",
                "Browser session handoff",
            ],
            "next_action": "Ask the user to choose a GitHub connection method.",
        }

    if not request.selected_repositories:
        return {
            "status": "needs_repository_selection",
            "mission_id": mission_id,
            "subagents": serialize_agents(orchestrator.plan("github-sync")),
            "next_action": "List authorized repositories and ask which ones to sync into GitLab.",
        }

    return {
        "status": "ready_to_sync",
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("github-sync")),
        "next_action": "Create matching GitLab projects and sync the selected repositories.",
    }


@app.post("/context/intake")
async def data_context_intake(request: DataContextRequest) -> dict[str, Any]:
    mission_id = f"data-context-{request.user_id}"
    orchestrator = MasterOrchestrator()
    vault = MongoVault()
    monitor = ArizeMonitor()
    pipeline = FivetranPipeline()

    if not request.allowed_sources:
        return {
            "status": "needs_consent",
            "mission_id": mission_id,
            "subagents": serialize_agents(orchestrator.plan("data-context")),
            "source_options": [
                "Google account via OAuth",
                "Apple account via Sign in with Apple",
                "GitHub via OAuth or vault-stored token",
                "Public social links",
                "User-uploaded exports",
                "Manual preferences questionnaire",
            ],
            "default_scopes": [
                "basic profile",
                "contacts selected by user",
                "calendar availability if scheduling is needed",
                "purchase/shipping preferences entered by user",
            ],
            "raw_passwords_stored": False,
        }

    await monitor.log_reasoning_trace(
        mission_id,
        [
            "Collect only user-approved sources.",
            "Normalize context into preferences and constraints.",
            "Store source, consent, expiry, and deletion metadata.",
        ],
    )
    await vault.store_mission_state(mission_id, {
        "allowed_sources": request.allowed_sources,
        "allowed_scopes": request.allowed_scopes,
        "context_expiry_days": request.context_expiry_days,
    })
    await pipeline.stream_mission_data(mission_id, {
        "mission": "data-context",
        "allowed_source_count": len(request.allowed_sources),
        "allowed_scope_count": len(request.allowed_scopes),
        "context_expiry_days": request.context_expiry_days,
    })

    return {
        "status": "context_ready",
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("data-context")),
        "next_action": "Use the approved context to personalize future missions.",
    }


@app.post("/missions/account-resolver")
async def account_resolver_mission(request: AccountResolverRequest) -> dict[str, Any]:
    mission_id = f"account-resolver-{request.user_id}-{request.service_name.lower().replace(' ', '-')}"
    orchestrator = MasterOrchestrator()
    vault = MongoVault()
    monitor = ArizeMonitor()
    search = ElasticSearch()
    pipeline = FivetranPipeline()

    await monitor.log_reasoning_trace(
        mission_id,
        [
            "Check the Mission Vault for an existing account or session.",
            "If missing, ask for explicit account creation approval.",
            "Deconstruct forms by text, accessible names, ARIA roles, and semantic input types.",
            "Do not expose DOM snippets, logs, passwords, or tokens to the user.",
            "Detect CAPTCHA, MFA, or email verification and pause for human completion.",
        ],
    )

    dom_pattern = await search.find_dom_pattern(
        request.service_url or request.service_name,
        "account_registration_or_login",
    )

    await vault.store_mission_state(mission_id, {
        "service_name": request.service_name,
        "service_url": request.service_url,
        "account_creation_allowed": request.account_creation_allowed,
        "known_account_hint": bool(request.known_account_hint),
        "authorized_credential_ref": bool(request.authorized_credential_ref),
        "authorized_session_ref": bool(request.authorized_session_ref),
        "required_action": request.required_action,
    })
    await pipeline.stream_mission_data(mission_id, {
        "mission": "account-resolver",
        "service_name": request.service_name,
        "account_creation_allowed": request.account_creation_allowed,
        "has_authorized_account_context": bool(
            request.known_account_hint or request.authorized_credential_ref or request.authorized_session_ref
        ),
    })

    if request.known_account_hint or request.authorized_credential_ref or request.authorized_session_ref:
        status = "account_context_available"
        next_action = "Use the existing account context or session handoff for the requested mission."
    elif request.account_creation_allowed:
        status = "ready_to_create_account"
        next_action = "Open the service, map the registration form, fill approved fields, and stop for human verification."
    else:
        status = "needs_account_permission"
        next_action = "Ask whether the user wants to connect an existing account or create a new one."

    return {
        "status": status,
        "mission_id": mission_id,
        "subagents": serialize_agents(orchestrator.plan("account-resolver")),
        "deconstruction_mode": "text_dom_accessibility_tree",
        "credential_policy": "authorized_vault_or_session_reference_only",
        "captcha_policy": "detect_pause_resume_after_human_completion",
        "user_visible_output": "high_level_status_only",
        "dom_pattern": dom_pattern,
        "next_action": next_action,
    }



