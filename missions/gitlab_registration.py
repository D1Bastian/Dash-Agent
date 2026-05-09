import argparse
import asyncio
import os
import re
import sys
from dataclasses import dataclass

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


SIGN_UP_URL = "https://gitlab.com/users/sign_up"


@dataclass
class RegistrationProfile:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


def mask(value: str, visible: int = 2) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * max(len(value) - visible, 4)}"


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        raise SystemExit(2)
    return value


def load_profile() -> RegistrationProfile:
    return RegistrationProfile(
        first_name=required_env("DASH_GITLAB_FIRST_NAME"),
        last_name=required_env("DASH_GITLAB_LAST_NAME"),
        username=required_env("DASH_GITLAB_USERNAME"),
        email=required_env("DASH_GITLAB_EMAIL"),
        password=required_env("DASH_GITLAB_PASSWORD"),
    )


def log(message: str) -> None:
    print(f"[dash-gitlab] {message}", flush=True)


async def click_optional_cookie_button(page) -> None:
    labels = [
        re.compile(r"accept all", re.I),
        re.compile(r"accept cookies", re.I),
        re.compile(r"accept", re.I),
    ]

    for label in labels:
        try:
            button = page.get_by_role("button", name=label).first
            await button.click(timeout=2000)
            log("Cookie prompt accepted.")
            return
        except PlaywrightTimeoutError:
            continue


async def fill_by_label(page, label: str, value: str, secret: bool = False) -> None:
    field = page.get_by_label(re.compile(f"^{re.escape(label)}$", re.I)).first
    await field.wait_for(state="visible", timeout=15000)
    await field.click()
    await field.fill("")
    await field.type(value, delay=25)
    await field.dispatch_event("input")
    await field.dispatch_event("change")

    held_value = await field.input_value()
    if held_value != value:
        raise RuntimeError(f"{label} did not retain the expected value")

    shown = mask(value) if secret else value
    log(f"Filled {label}: {shown}")


async def detect_human_gate(page) -> str | None:
    selectors = [
        "iframe[src*='captcha']",
        "iframe[src*='hcaptcha']",
        "iframe[src*='recaptcha']",
        ".g-recaptcha",
        "[data-sitekey]",
        "[class*='captcha' i]",
        "[id*='captcha' i]",
    ]

    for selector in selectors:
        if await page.locator(selector).count() > 0:
            return "CAPTCHA challenge detected"

    try:
        body_text = (await page.locator("body").inner_text(timeout=3000)).lower()
    except PlaywrightTimeoutError:
        return None

    gate_terms = [
        "captcha",
        "verification email",
        "confirm your email",
        "check your email",
        "verify your account",
        "cloudflare",
        "multi-factor",
    ]
    for term in gate_terms:
        if term in body_text:
            return f"Verification checkpoint detected: {term}"

    return None


async def submit_registration(page) -> None:
    continue_button = page.get_by_role("button", name=re.compile(r"^continue$", re.I)).first
    await continue_button.wait_for(state="visible", timeout=15000)
    await continue_button.click()
    log("Submitted registration form.")


async def wait_for_manual_checkpoint(page, reason: str) -> None:
    log(f"{reason}. Complete it in the browser, then press Enter here to resume.")
    await asyncio.to_thread(input)
    await page.wait_for_load_state("domcontentloaded")


async def run(profile: RegistrationProfile, headless: bool) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless, slow_mo=80)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        log("Opening GitLab registration.")
        await page.goto(SIGN_UP_URL, wait_until="domcontentloaded")
        await click_optional_cookie_button(page)

        log("Mapping fields by accessible label.")
        await fill_by_label(page, "First name", profile.first_name)
        await fill_by_label(page, "Last name", profile.last_name)
        await fill_by_label(page, "Username", profile.username)
        await fill_by_label(page, "Email", profile.email, secret=True)
        await fill_by_label(page, "Password", profile.password, secret=True)

        await submit_registration(page)
        await page.wait_for_timeout(3000)

        gate = await detect_human_gate(page)
        if gate:
            await wait_for_manual_checkpoint(page, gate)

        log(f"Current browser state: {page.url}")
        final_gate = await detect_human_gate(page)
        if final_gate:
            log(f"Still waiting on checkpoint: {final_gate}")
        else:
            log("Registration flow advanced past the initial form.")

        if headless:
            await browser.close()
        else:
            log("Browser left open for the demo recording.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Dash GitLab registration mission.")
    parser.add_argument("--headless", action="store_true", help="Run without showing the browser.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(load_profile(), headless=args.headless))
