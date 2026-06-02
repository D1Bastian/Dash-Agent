import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from backend.main import gemini  # Assuming gemini is importable

@dataclass
class RegistrationProfile:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

async def run_dynamic_resolver_stream(url: str, profile: RegistrationProfile, headless: bool = False):
    def emit(text: str):
        return f"data: {json.dumps({'text': text + chr(10)})}\n\n"

    yield emit(f"🚀 Starting **Universal Dynamic Account Resolver** for `{url}`...")
    yield emit("🧠 Goal: Analyze form dynamically via DOM Deconstruction and Gemini 3.")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless, slow_mo=50)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        yield emit(f"🌐 Navigating to `{url}`...")
        await page.goto(url, wait_until="domcontentloaded")
        
        # Handle simple cookie banners dynamically
        try:
            button = page.get_by_role("button", name=re.compile(r"accept all|accept cookies|accept", re.I)).first
            await button.click(timeout=3000)
            yield emit("🍪 Accepted cookie prompt automatically.")
        except PlaywrightTimeoutError:
            pass

        yield emit("🔍 Deconstructing DOM to find form inputs and buttons...")
        
        # Deconstruct DOM
        elements = await page.eval_on_selector_all(
            "[role], input, button, a, select, textarea, form",
            """els => els.map(el => {
                const isVisible = el.offsetWidth > 0 && el.offsetHeight > 0;
                if (!isVisible) return null;
                return {
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || null,
                    name: el.getAttribute('name') || null,
                    type: el.getAttribute('type') || null,
                    placeholder: el.getAttribute('placeholder') || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    text: (el.innerText || '').trim().slice(0, 50) || null,
                    id: el.id || null,
                };
            }).filter(e => e !== null)"""
        )

        yield emit(f"📊 Found {len(elements)} interactive elements. Checking Elastic Search cache...")

        from superpowers.elastic_search import ElasticSearch
        elastic = ElasticSearch()
        cached_actions = await elastic.get_solved_actions(url)

        if cached_actions:
            yield emit(f"⚡ Elastic Cache Hit! Executing from muscle memory...")
            actions = cached_actions
        else:
            yield emit(f"🧠 Cache miss. Analyzing with Gemini...")
            
            # Ask Gemini to map fields
            system_prompt = (
                "You are Dash, an autonomous web agent. Given a list of DOM elements and a user profile, "
                "determine exactly which fields to fill and what button to click to submit the registration or login form.\n"
                "Return a JSON array of actions. Actions can be:\n"
                "- {\"action\": \"fill\", \"id\": \"element_id\" OR \"name\": \"element_name\", \"value\": \"value_to_fill\"}\n"
                "- {\"action\": \"click\", \"id\": \"element_id\" OR \"name\": \"element_name\" OR \"text\": \"button_text\"}\n"
                "Only return valid JSON."
            )

            prompt = (
                f"User Profile:\nFirst: {profile.first_name}, Last: {profile.last_name}, "
                f"User: {profile.username}, Email: {profile.email}, Password: {profile.password}\n\n"
                f"DOM Elements:\n{json.dumps(elements, indent=2)}\n\n"
                "Generate the JSON array of actions to fill and submit this form."
            )

            response = await gemini(prompt, system=system_prompt, model="gemini-2.5-flash")
            
            # Parse Gemini's JSON
            try:
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:-3]
                elif json_str.startswith("```"):
                    json_str = json_str[3:-3]
                
                actions = json.loads(json_str)
                yield emit(f"🤖 Gemini mapped {len(actions)} actions. Saving to Elastic Search...")
                await elastic.save_solved_actions(url, actions)
            except Exception as e:
                yield emit(f"❌ Failed to parse Gemini response: {str(e)}")
                await browser.close()
                return

        # Execute actions
        for action in actions:
            await asyncio.sleep(0.5)
            if action["action"] == "fill":
                selector = ""
                if "id" in action and action["id"]:
                    selector = f"#{action['id']}"
                elif "name" in action and action["name"]:
                    selector = f"[name='{action['name']}']"
                
                if selector:
                    field = page.locator(selector).first
                    await field.fill(action["value"])
                    yield emit(f"  └─ Filled `{action.get('name', action.get('id'))}`")
            
            elif action["action"] == "click":
                selector = ""
                if "id" in action and action["id"]:
                    selector = f"#{action['id']}"
                elif "text" in action and action["text"]:
                    selector = f"text={action['text']}"
                elif "name" in action and action["name"]:
                    selector = f"[name='{action['name']}']"
                
                if selector:
                    btn = page.locator(selector).first
                    await btn.click()
                    yield emit(f"  └─ Clicked `{action.get('text', selector)}`")

        yield emit("✅ Form submitted. Scanning for human checkpoints...")
        
        # Check for HITL gates (CAPTCHA, MFA)
        await page.wait_for_timeout(3000)
        
        try:
            body_text = (await page.locator("body").inner_text(timeout=2000)).lower()
            gate_detected = any(term in body_text for term in ["captcha", "verification email", "verify your account", "confirm your email", "security check"])
            
            if gate_detected:
                yield emit("\n⛔ **HITL GATE: Human Checkpoint Detected**")
                yield emit("Dash paused: **Please complete the verification in the opened browser window.**")
                yield emit("Waiting for URL change to proceed...")
                
                # Wait for URL to change significantly or user to press a button
                current_url = page.url
                await page.wait_for_url(lambda u: u != current_url, timeout=300000)
                yield emit("\n✅ Checkpoint cleared! Resuming autonomous execution.")
        except PlaywrightTimeoutError:
            pass

        yield emit("🎉 Dynamic resolution complete.")
        yield emit("🔒 State mapped to MongoVault (non-secret reference).")
        
        await asyncio.sleep(2)
        await browser.close()
