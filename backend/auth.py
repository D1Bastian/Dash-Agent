"""
Google OAuth + Gemini-on-behalf-of-user flow.

Flow:
  1. Frontend calls GET /auth/google/url  -> gets the Google OAuth URL
  2. User approves in Google popup        -> Google redirects to /auth/google/callback?code=...
  3. Backend exchanges code for tokens    -> stores refresh_token in MongoDB vault
  4. Frontend calls POST /mission/execute with Authorization: Bearer <access_token>
  5. Backend uses that token to call Gemini API on behalf of the user
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI         = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Scopes: identity + Gemini (Generative Language API)
SCOPES = " ".join([
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/generative-language",   # Gemini API
    "https://www.googleapis.com/auth/cloud-platform.read-only",
])

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


# -- 1. Get the Google OAuth login URL --------------------------------------
@router.get("/google/url")
async def google_auth_url():
    if not GOOGLE_CLIENT_ID:
        # Demo mode: no OAuth configured
        return JSONResponse({"url": None, "demo_mode": True})
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",   # get refresh_token
        "prompt":        "consent",   # always show consent so we get refresh_token
    }
    from urllib.parse import urlencode
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"url": url, "demo_mode": False}


# -- 2. OAuth callback - exchange code for tokens ---------------------------
@router.get("/google/callback")
async def google_callback(code: str, request: Request):
    if not GOOGLE_CLIENT_ID:
        return RedirectResponse(f"{FRONTEND_URL}?auth=demo")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  REDIRECT_URI,
                "grant_type":    "authorization_code",
            },
        )
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=token_data["error"])

    access_token  = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    id_token      = token_data.get("id_token")

    # Decode id_token (JWT) to get user info without extra request
    import base64, json as _json
    payload = id_token.split(".")[1] if id_token else ""
    padding = 4 - len(payload) % 4
    try:
        user_info = _json.loads(base64.b64decode(payload + "=" * padding))
    except Exception:
        user_info = {}

    user_id = user_info.get("sub", "unknown")
    email   = user_info.get("email", "")
    name    = user_info.get("name", "")

    # Store refresh_token in MongoDB vault (never exposed to frontend)
    try:
        from superpowers.mongo_vault import MongoVault
        vault = MongoVault()
        await vault.register_user(user_id, {
            "display_name":   name,
            "primary_email":  email,
            "auth_provider":  "google",
            "authorized_sources": ["google"],
            "mission_goals":  ["gift-scout", "travel", "account-resolver", "social-manager"],
        })
        # Store the refresh token as a vault secret reference (never returned to client)
        await vault.store_context_source(user_id, {
            "provider":       "google",
            "scope":          "gemini+identity",
            "refresh_token":  refresh_token,   # encrypted at rest in Mongo
            "status":         "active",
        })
    except Exception:
        pass  # vault unavailable - still let user in (demo mode)

    # Redirect to frontend with a short-lived access token in the URL fragment
    # (access_token expires in 1h; frontend uses it for Gemini calls via /mission/execute)
    redirect = f"{FRONTEND_URL}#access_token={access_token}&user_id={user_id}&name={name}&email={email}"
    return RedirectResponse(redirect)


# -- 3. Refresh the access token using the stored refresh_token -------------
class RefreshRequest(BaseModel):
    user_id: str

@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    if not GOOGLE_CLIENT_ID:
        return {"access_token": "demo-token", "demo_mode": True}

    try:
        from superpowers.mongo_vault import MongoVault
        vault = MongoVault()
        ctx = await vault.get_context_source(body.user_id, "google")
        refresh_tok = ctx.get("refresh_token") if ctx else None
    except Exception:
        raise HTTPException(status_code=404, detail="No stored token for this user.")

    if not refresh_tok:
        raise HTTPException(status_code=401, detail="No refresh token - user must re-authorise.")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_tok,
                "grant_type":    "refresh_token",
            },
        )
        data = resp.json()

    if "error" in data:
        raise HTTPException(status_code=401, detail=data["error"])

    return {"access_token": data["access_token"], "expires_in": data.get("expires_in", 3600)}


# -- 4. Proxy a Gemini request using the user own token --------------------
class GeminiRequest(BaseModel):
    user_id:   str
    prompt:    str
    model:     str = "gemini-2.0-flash"
    mission:   str = "general"

@router.post("/gemini/generate")
async def gemini_generate(body: GeminiRequest, request: Request):
    """
    Calls Gemini using the user own Google OAuth access token.
    The Authorization header must carry Bearer <access_token>.
    Falls back to demo response if no token is present (local dev).
    """
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "").strip()

    if not access_token or access_token == "demo-token":
        # Demo mode - return a canned response
        return {
            "status": "demo",
            "text": f"[Demo mode] Gemini would respond to: {body.prompt[:80]}...",
            "mission": body.mission,
        }

    payload = {
        "contents": [{"role": "user", "parts": [{"text": body.prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GEMINI_API_BASE}/models/{body.model}:generateContent",
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]

    return {"status": "ok", "text": text, "mission": body.mission, "model": body.model}
