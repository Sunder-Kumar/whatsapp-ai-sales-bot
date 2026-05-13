import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from bot.session import WhatsAppSession

class MessageMonitor:
    def __init__(self, session: WhatsAppSession, redis_url: str):
        self.session = session
        self.redis_url = redis_url
        self.redis = None

    async def start(self):
        self.redis = await redis.from_url(self.redis_url)
        print("Message Monitor started.")
        
        while True:
            try:
                await self.check_for_messages()
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            await asyncio.sleep(1.5)

    async def check_for_messages(self):
        page = await self.session.get_page()
        
        # 1. Find chats with unread badges
        # Selector for unread badge: span[aria-label*='unread']
        unread_chats = await page.query_selector_all("span[aria-label*='unread']")
        
        for badge in unread_chats:
            # Navigate to the chat
            # This is a simplification; in practice, you'd click the parent chat element
            chat_element = await badge.evaluate_handle("el => el.closest('div[role=\"row\"]')")
            if chat_element:
                await chat_element.click()
                await asyncio.sleep(0.5) # Wait for chat to load
                
                # 2. Identify the sender (simplified)
                # You'd typically extract the phone number from the header or chat info
                header = await page.query_selector("header")
                contact_info = await header.inner_text() if header else "Unknown"
                phone = self.extract_phone(contact_info)
                
                # 3. Get last message bubbles
                # Selector: div.message-in
                messages = await page.query_selector_all("div.message-in")
                if messages:
                    last_msg = messages[-1]
                    content = await last_msg.inner_text()
                    
                    # 4. Detect type (simplified)
                    msg_type = "text"
                    if await last_msg.query_selector("span[data-icon='audio-play']"):
                        msg_type = "voice_note"
                    elif await last_msg.query_selector("img"):
                        msg_type = "image"
                    
                    # 5. Push to Redis queue
                    payload = {
                        "phone": phone,
                        "type": msg_type,
                        "content": content,
                        "timestamp": datetime.now().isoformat(),
                        "chat_name": contact_info.split('\n')[0]
                    }
                    
                    await self.redis.lpush("incoming_queue", json.dumps(payload))
                    print(f"Pushed message from {phone} to queue.")

    def extract_phone(self, text):
        # Very basic extraction; replace with regex for real world use
        # WhatsApp usually shows phone or name in header
        return text.split('\n')[0].replace(" ", "").replace("-", "")

async def run_monitor():
    # This is for standalone testing
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    session = WhatsAppSession(headless=False)
    await session.start()
    
    if await session.is_logged_in():
        monitor = MessageMonitor(session, os.getenv("REDIS_URL", "redis://localhost:6379"))
        await monitor.start()
    else:
        print("Not logged in. Please run scanner.py first.")
    
    await session.stop()

if __name__ == "__main__":
    asyncio.run(run_monitor())
