import asyncio
import random
from bot.session import WhatsAppSession

class MessageSender:
    def __init__(self, session: WhatsAppSession):
        self.session = session

    async def send_text(self, phone: str, message: str):
        """
        Sends a text message with human-like behavior.
        """
        page = await self.session.get_page()
        
        # 1. Reading delay (simulating the bot reading the incoming message)
        reading_delay = random.uniform(0.8, 2.0)
        await asyncio.sleep(reading_delay)

        # 2. Thinking delay (before starting to type)
        thinking_delay = random.uniform(1.0, 2.5)
        await asyncio.sleep(thinking_delay)

        # Navigate to chat or ensure it's focused
        # Note: In a real production loop, the monitor might already have the chat open.
        # But for reliability, we can use the URL method.
        url = f"https://web.whatsapp.com/send?phone={phone}"
        if page.url != url:
            await page.goto(url)
            await page.wait_for_selector("div[contenteditable='true'][data-tab='10']", timeout=15000)

        # 3. Typing simulation
        # Calculate typing delay proportional to length
        chars_per_second = random.uniform(150, 220)
        typing_delay = len(message) / chars_per_second
        typing_delay = min(typing_delay, 8.0) # Cap at 8 seconds

        # Focus input and show "typing..."
        # Selector for WhatsApp Web input field
        input_selector = "div[contenteditable='true'][data-tab='10']"
        await page.click(input_selector)
        await asyncio.sleep(typing_delay)

        # 4. Actually send the message
        # We can either type it or paste it. For speed/reliability we use fill() then press Enter.
        await page.fill(input_selector, message)
        await page.press(input_selector, "Enter")

        print(f"Message sent to {phone} with {typing_delay:.2f}s typing simulation.")
        return True

    async def send_delivery_message(self, phone: str, package_info: dict):
        """
        Sends the automated delivery message with credentials.
        """
        try:
            with open("whatsapp-bot/templates/delivery.txt", "r", encoding="utf-8") as f:
                template = f.read()
            
            message = template.format(
                package_name=package_info.get("package_name"),
                login_email=package_info.get("login_email"),
                login_password=package_info.get("login_password"),
                profile_pin=package_info.get("profile_pin", "None")
            )
            
            return await self.send_text(phone, message)
        except Exception as e:
            print(f"Error sending delivery message: {e}")
            return False

    async def send_multipart_reply(self, phone: str, messages: list):
        """
        Sends multiple messages with short gaps between them.
        """
        for msg in messages:
            await self.send_text(phone, msg)
            # Gap between multi-part messages
            await asyncio.sleep(random.uniform(1.5, 3.0))
