import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Path where the WhatsApp session will be saved
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session")

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
        # Headless=False is required to see the QR code
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        await page.goto("https://web.whatsapp.com")

        # Detect whether the session is already logged in.
        logged_in = False
        try:
            await page.wait_for_selector('#pane-side, div[contenteditable="true"][data-tab="3"]', timeout=10000)
            logged_in = True
        except:
            logged_in = False

        if not logged_in:
            print("\n" + "="*50)
            print("ACTION REQUIRED: Scan the QR code on your screen.")
            print("="*50 + "\n")

        try:
            # Wait up to 2 minutes for login/chat interface to load
            if not logged_in:
                await page.wait_for_selector('#pane-side, div[contenteditable="true"][data-tab="3"]', timeout=120000)
            print("Login successful! Session saved.")
        except Exception as e:
            qr_present = await page.query_selector("canvas[aria-label='Scan me!']")
            if qr_present:
                print("Login timeout or failed: QR code still displayed. Please scan again.")
            else:
                print(f"Login timeout or failed: {e}")
        finally:
            await browser_context.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_scanner())
