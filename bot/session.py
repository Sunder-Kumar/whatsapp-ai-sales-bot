import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

SESSION_DIR = "whatsapp-bot/session"

class WhatsAppSession:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser_context = None
        self.page = None
        self.playwright = None

    async def start(self):
        """Starts the persistent browser context."""
        self.playwright = await async_playwright().start()
        
        headless_env = os.getenv("HEADLESS", "True").lower() == "true"
        # If user passed headless=False in init, override env
        is_headless = self.headless and headless_env

        self.browser_context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=is_headless,
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        self.page = await self.browser_context.new_page()
        await self.page.goto("https://web.whatsapp.com")
        print("WhatsApp Web loaded.")

    async def stop(self):
        """Stops the browser and playwright."""
        if self.browser_context:
            await self.browser_context.close()
        if self.playwright:
            await self.playwright.stop()
        print("WhatsApp session stopped.")

    async def is_logged_in(self):
        """Checks if the user is logged into WhatsApp Web."""
        try:
            # Check for the search bar or chat list
            await self.page.wait_for_selector("div[contenteditable='true'][data-tab='3']", timeout=10000)
            return True
        except:
            return False

    async def get_page(self):
        return self.page
