import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Path where the WhatsApp session will be saved
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session")

async def _is_logged_in(page):
    if await page.query_selector("canvas[aria-label*='Scan']"):
        return False

    selectors = [
        '#pane-side',
        'div[contenteditable="true"][data-tab="3"]',
        'div[contenteditable="true"][data-tab="10"]',
        'div[title="Search or start new chat"]',
        'div[aria-label="Search or start new chat"]'
    ]
    for selector in selectors:
        if await page.query_selector(selector):
            return True
    return False

async def run_scanner():
    """
    Launches a browser for the user to scan the WhatsApp QR code.
    Saves the session to SESSION_DIR.
    """
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
        print(f"Created session directory: {SESSION_DIR}")
    else:
        print(f"Using session directory: {SESSION_DIR}")

    async with async_playwright() as p:
        print("Launching browser for QR scan...")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        await page.goto("https://web.whatsapp.com")

        logged_in = await _is_logged_in(page)
        if not logged_in:
            print("\n" + "="*50)
            print("ACTION REQUIRED: Scan the QR code on your screen.")
            print("="*50 + "\n")

        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_selector(
                '#pane-side, div[contenteditable="true"][data-tab="3"], div[contenteditable="true"][data-tab="10"], div[title="Search or start new chat"], div[aria-label="Search or start new chat"]',
                timeout=120000
            )
            current_url = page.url
            page_title = await page.title()
            print(f"Page URL after login: {current_url}")
            print(f"Page title after login: {page_title}")

            if await _is_logged_in(page):
                print("Login successful! Session saved.")
                print(f"Session files stored under: {SESSION_DIR}")
            else:
                print("Login completed, but WhatsApp did not show the expected interface. Please try again.")
        except Exception as e:
            qr_present = await page.query_selector("canvas[aria-label*='Scan']")
            if qr_present:
                print("Login timeout or failed: QR code still displayed. Please scan again.")
            else:
                print(f"Login timeout or failed: {e}")
        finally:
            await browser_context.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_scanner())
