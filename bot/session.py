import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session")
LOGIN_SELECTORS = [
    "#pane-side",
    "div[contenteditable='true'][data-tab='3']",
    "div[contenteditable='true'][data-tab='10']",
    "div[title='Search or start new chat']",
    "div[aria-label='Search or start new chat']",
]

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
        
        self.page = self.browser_context.pages[0] if self.browser_context.pages else await self.browser_context.new_page()
        if self.page.url != "https://web.whatsapp.com/":
            await self.page.goto("https://web.whatsapp.com")

        await self.wait_until_ready()

        current_url = self.page.url
        print(f"WhatsApp Web loaded at: {current_url}")

        if not await self.is_logged_in():
            print("WhatsApp session not currently logged in. Please run python bot/scanner.py and scan the QR code.")
        else:
            print("WhatsApp session is logged in.")

    async def stop(self):
        """Stops the browser and playwright."""
        if self.browser_context:
            await self.browser_context.close()
        if self.playwright:
            await self.playwright.stop()
        print("WhatsApp session stopped.")

    async def is_logged_in(self):
        """Checks if the user is logged into WhatsApp Web."""
        for selector in LOGIN_SELECTORS:
            try:
                if await self.page.query_selector(selector):
                    return True
            except Exception:
                continue
        return False

    async def wait_until_ready(self, timeout=120000):
        """Waits for WhatsApp Web to show the logged-in UI before health checks."""
        try:
            await self.page.wait_for_selector(", ".join(LOGIN_SELECTORS), timeout=timeout)
        except Exception:
            try:
                await self.page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

    async def get_page(self):
        return self.page
