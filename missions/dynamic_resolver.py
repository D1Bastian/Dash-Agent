import asyncio
import json
import os
import re
from dataclasses import dataclass

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from backend.main import GEMINI_MODEL, gemini


@dataclass
class RegistrationProfile:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


def _build_profile_from_env() -> RegistrationProfile | None:
    """Build a registration profile from environment variables.
    
    Set these in render.yaml / .env.local:
        DASH_REG_FIRST_NAME
        DASH_REG_LAST_NAME
        DASH_REG_USERNAME
        DASH_REG_EMAIL
        DASH_REG_PASSWORD
    """
    first = os.getenv("DASH_REG_FIRST_NAME")
    last = os.getenv("DASH_REG_LAST_NAME")
    username = os.getenv("DASH_REG_USERNAME")
    email = os.getenv("DASH_REG_EMAIL")
    password = os.getenv("DASH_REG_PASSWORD")

    if all([first, last, username, email, password]):
        return RegistrationProfile(
            first_name=first,
            last_name=last,
            username=username,
            email=email,
            password=password,
        )
    return None


async def run_dynamic_resolver_stream(
    url: str,
    profile: RegistrationProfile | None = None,
    headless: bool = True,
):
    """Full LLM-driven web agent. Navigates to `url`, lets Gemini read and map
    the form semantics, fills the approved fields, and streams high-level
    status. No hardcoded values — all identity comes from the vault/env."""

    def emit(text: str):
        return f"data: {json.dumps({'text': text + chr(10)})}\n\n"

    # ── Phase 0: resolve profile ──────────────────────────────────────────────
    if profile is None:
        profile = _build_profile_from_env()

    if profile is None:
        yield emit(
            "⚠️  No registration profile found. "
            "Set DASH_REG_FIRST_NAME / DASH_REG_LAST_NAME / DASH_REG_USERNAME / "
            "DASH_REG_EMAIL / DASH_REG_PASSWORD as environment variables, "
            "or save a profile to the Mission Vault first."
        )
        return

    yield emit(f"🚀 **Dash Universal Agent** — target: `{url}`")
    yield emit("🧠 Gemini will read the page, map the form, and decide every action.")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless, slow_mo=60)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # ── Phase 1: DISCOVER ────────────────────────────────────────────────
        yield emit(f"🌐 Navigating to `{url}` …")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            yield emit(f"❌ Navigation failed: {e}")
            await browser.close()
            return

        # Dismiss cookie banners automatically
        try:
            btn = page.get_by_role(
                "button", name=re.compile(r"accept all|accept cookies|accept", re.I)
            ).first
            await btn.click(timeout=3000)
            yield emit("🍪 Cookie banner dismissed.")
        except PlaywrightTimeoutError:
            pass

        await page.wait_for_timeout(1500)

        yield emit("🔍 Deconstructing visible interactive elements …")
        elements = await page.eval_on_selector_all(
            "[role], input, button, a, select, textarea, form",
            """els => els.map(el => {
                const r = el.getBoundingClientRect();
                const visible = r.width > 0 && r.height > 0 && r.top < window.innerHeight;
                if (!visible) return null;
                return {
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || null,
                    name: el.getAttribute('name') || null,
                    type: el.getAttribute('type') || null,
                    placeholder: el.getAttribute('placeholder') || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    text: (el.innerText || '').trim().slice(0, 60) || null,
                    id: el.id || null,
                    autocomplete: el.getAttribute('autocomplete') || null,
                };
            }).filter(e => e !== null)""",
        )
        yield emit(f"📋 Found **{len(elements)}** visible interactive elements.")

        # ── Phase 2: PLAN (Elastic cache → Gemini) ───────────────────────────
        from superpowers.elastic_search import ElasticSearch
        elastic = ElasticSearch()
        cached = await elastic.get_solved_actions(url)

        if cached:
            yield emit("⚡ Elastic cache hit — reusing prior action mapping.")
            actions = cached
        else:
            yield emit("🤖 Asking Gemini to analyse the form and produce an action plan …")
            actions = await _map_actions_with_gemini(elements, url)
            if not actions:
                yield emit(
                    "⚠️  Gemini could not produce a safe action mapping. "
                    "Mission paused for human review."
                )
                await browser.close()
                return
            yield emit(f"✅ Gemini mapped **{len(actions)}** actions. Saving to Elastic …")
            await elastic.save_solved_actions(url, actions)

        # ── Phase 3: FORM FILL ───────────────────────────────────────────────
        yield emit("\n**Phase 3 — Form Fill**")
        async for chunk in _execute_actions(page, actions, profile, emit):
            yield chunk

        # ── Phase 4: VERIFY ──────────────────────────────────────────────────
        yield emit("\n**Phase 4 — Scanning for human checkpoints …**")
        await page.wait_for_timeout(3000)

        try:
            body = (await page.locator("body").inner_text(timeout=3000)).lower()
        except Exception:
            body = ""

        gate_terms = [
            "captcha",
            "verification email",
            "verify your account",
            "confirm your email",
            "security check",
            "multi-factor",
            "two-factor",
            "check your inbox",
        ]
        if any(t in body for t in gate_terms):
            yield emit("\n⛔ **HITL GATE — Human Checkpoint Detected**")
            yield emit(
                "Dash has paused. Please complete the verification "
                "(CAPTCHA / email / MFA) in the browser window."
            )
            yield emit("Waiting for the page to change before resuming …")
            try:
                current = page.url
                await page.wait_for_url(
                    lambda u: u != current, timeout=300_000
                )
                yield emit("\n✅ Checkpoint cleared — resuming.")
            except PlaywrightTimeoutError:
                yield emit("❌ Timed out waiting for human checkpoint. Mission aborted.")
                await browser.close()
                return
        else:
            yield emit("✅ No human checkpoint detected — proceeding.")

        # ── Phase 5: SAVE ────────────────────────────────────────────────────
        yield emit("\n**Phase 5 — Save**")
        try:
            from superpowers.mongo_vault import MongoVault
            vault = MongoVault()
            await vault.store_mission_state(
                f"resolver-{profile.username}",
                {
                    "url": url,
                    "username": profile.username,
                    "status": "completed",
                    "final_url": page.url,
                },
            )
            yield emit("💾 Mission state saved to **MongoVault** (no secrets stored).")
        except Exception as e:
            yield emit(f"⚠️  Vault save skipped: {e}")

        yield emit(f"\n🏁 **Mission complete.** Final URL: `{page.url}`")
        await asyncio.sleep(1)
        await browser.close()


# ── LLM action planner ────────────────────────────────────────────────────────

async def _map_actions_with_gemini(elements: list[dict], url: str) -> list[dict]:
    """Ask Gemini to read the DOM snapshot and return a JSON action plan."""
    system_prompt = (
        "You are Dash, an autonomous web agent. "
        "You receive a snapshot of visible DOM elements from a web page. "
        "Your job is to determine the exact sequence of actions needed to "
        "complete a registration or account-creation form on that page. "
        "\n\n"
        "Rules:\n"
        "- Return ONLY a valid JSON array, no markdown fences, no explanation.\n"
        "- Fill actions must reference a value_key, never a raw value.\n"
        "- Allowed value_keys: first_name, last_name, username, email, password.\n"
        "- Action schema:\n"
        '  {"action":"fill","id":"<id>","name":"<name>","ariaLabel":"<label>",'
        '"placeholder":"<ph>","value_key":"<key>"}\n'
        '  {"action":"click","id":"<id>","name":"<name>","text":"<button text>"}\n'
        "- Only include inputs that are visible and relevant to registration.\n"
        "- Include a final click action for the submit/register/continue button.\n"
        "- If you cannot safely determine the correct mapping, return [].\n"
    )
    prompt = (
        f"Target URL: {url}\n"
        "Available profile keys: first_name, last_name, username, email, password.\n\n"
        f"DOM snapshot:\n{json.dumps(elements, indent=2)}"
    )

    try:
        response = await gemini(prompt, system=system_prompt, model=GEMINI_MODEL)
    except Exception:
        return []

    raw = response.strip()
    # Strip markdown fences if Gemini adds them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        actions = json.loads(raw)
        return actions if isinstance(actions, list) else []
    except json.JSONDecodeError:
        return []


# ── Action executor ───────────────────────────────────────────────────────────

async def _execute_actions(page, actions: list[dict], profile: RegistrationProfile, emit):
    values = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "username": profile.username,
        "email": profile.email,
        "password": profile.password,
    }

    for action in actions:
        await asyncio.sleep(0.4)
        act = action.get("action")
        label = (
            action.get("ariaLabel")
            or action.get("placeholder")
            or action.get("name")
            or action.get("id")
            or action.get("text")
            or "field"
        )

        if act == "fill":
            locator = _field_locator(page, action)
            key = action.get("value_key", "")
            value = values.get(key)

            if not locator or not value:
                yield emit(f"  ⏭  Skipped `{label}` — no approved value available.")
                continue

            try:
                await locator.wait_for(state="visible", timeout=5000)
                await locator.click()
                await locator.fill("")
                await locator.type(value, delay=35)
                await locator.dispatch_event("input")
                await locator.dispatch_event("change")
                shown = "***" if key in {"password", "email"} else key
                yield emit(f"  ✍️  Filled `{label}` from profile key `{shown}`.")
            except Exception as e:
                yield emit(f"  ⚠️  Could not fill `{label}`: {e}")

        elif act == "click":
            locator = _click_locator(page, action)
            if not locator:
                yield emit(f"  ⏭  Skipped click `{label}` — no target found.")
                continue
            try:
                await locator.click(timeout=5000)
                yield emit(f"  🖱️  Clicked `{label}`.")
                await page.wait_for_timeout(1000)
            except Exception as e:
                yield emit(f"  ⚠️  Click `{label}` failed: {e}")


def _field_locator(page, action: dict):
    if action.get("id"):
        return page.locator(f"#{action['id']}").first
    if action.get("name"):
        return page.locator(f"[name='{action['name']}']").first
    if action.get("ariaLabel"):
        return page.get_by_label(re.compile(re.escape(action["ariaLabel"]), re.I)).first
    if action.get("placeholder"):
        return page.get_by_placeholder(re.compile(re.escape(action["placeholder"]), re.I)).first
    return None


def _click_locator(page, action: dict):
    if action.get("id"):
        return page.locator(f"#{action['id']}").first
    if action.get("name"):
        return page.locator(f"[name='{action['name']}']").first
    if action.get("text"):
        return page.get_by_role("button", name=re.compile(re.escape(action["text"]), re.I)).first
    return None
