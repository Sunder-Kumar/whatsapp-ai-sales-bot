import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Path where the WhatsApp session will be saved
SESSION_DIR = "whatsapp-bot/session"

async def run_scanner():
    """
    Launches a browser for the user to scan the WhatsApp QR code.
    Saves the session to SESSION_DIR.
    """
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
        print(f"Created session directory: {SESSION_DIR}")

    async with async_playwright() as p:
        print("Launching browser for QR scan...")
        # Headless=False is required to see the QR code
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        page = await browser.new_page()
        await page.goto("https://web.whatsapp.com")

        print("\n" + "="*50)
        print("ACTION REQUIRED: Scan the QR code on your screen.")
        print("="*50 + "\n")

        # Wait for the user to scan and for the main interface to load
        # We look for a selector that only appears after login, e.g., the search bar or chat list
        try:
            # Wait up to 2 minutes for login
            await page.wait_for_selector("div[contenteditable='true'][data-tab='3']", timeout=120000)
            print("Login successful! Session saved.")
        except Exception as e:
            print(f"Login timeout or failed: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_scanner())
