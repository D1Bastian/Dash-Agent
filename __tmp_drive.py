import asyncio, sys
from playwright.async_api import async_playwright

URL = "http://127.0.0.1:8765/"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()

        # collect console + network errors
        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_msgs.append(f"[PAGEERROR] {exc}"))
        bad_responses = []
        page.on("response", lambda r: bad_responses.append((r.status, r.url)) if r.status >= 400 else None)

        await page.goto(URL, wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(800)

        # Screenshot 1: login screen
        await page.screenshot(path=r"C:\dev\infinite-action-agent\__tmp_login.png", full_page=True)

        # Click "Continue with Demo" — find by text
        try:
            await page.get_by_text("Continue with Demo", exact=False).first.click(timeout=3000)
        except Exception as e:
            console_msgs.append(f"[CLICK-FAIL] {e!r}")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"C:\dev\infinite-action-agent\__tmp_dashboard.png", full_page=True)

        # Body scroll dims
        body_scroll = await page.evaluate("""() => ({
            scrollHeight: document.body.scrollHeight,
            clientHeight: document.body.clientHeight,
            scrollWidth:  document.body.scrollWidth,
            innerHeight:  window.innerHeight,
            overflowY:    getComputedStyle(document.body).overflowY,
            htmlOverflow: getComputedStyle(document.documentElement).overflowY,
        })""")
        print("BODY_SCROLL", body_scroll)

        # Find the Safety defaults heading
        try:
            sd = page.locator("h3", has_text="Safety defaults").first
            sd_box = await sd.bounding_box()
            sd_color = await sd.evaluate("el => getComputedStyle(el).color")
            sd_parent_bg = await sd.evaluate("el => getComputedStyle(el.closest('.detail-card')).backgroundColor")
            print("SAFETY", sd_box, "color=", sd_color, "parent_bg=", sd_parent_bg)
        except Exception as e:
            print("SAFETY_LOCATOR_FAIL", repr(e))

        # Find the profile fields
        for name in ["Display name", "Primary email", "Default country", "Preferred currency"]:
            try:
                loc = page.locator("label.field", has_text=name).first
                box = await loc.bounding_box()
                print(f"FIELD[{name}]", box)
            except Exception as e:
                print(f"FIELD[{name}] FAIL", repr(e))

        # Find "Test GitLab Sync" button
        try:
            btn = page.get_by_text("Test GitLab Sync", exact=False).first
            box = await btn.bounding_box()
            print("GITLAB_BTN", box)
        except Exception as e:
            print("GITLAB_BTN FAIL", repr(e))

        print("---CONSOLE---")
        for m in console_msgs:
            print(m)
        print("---BAD_RESPONSES---")
        for code, url in bad_responses:
            print(code, url)

        await browser.close()

asyncio.run(main())
