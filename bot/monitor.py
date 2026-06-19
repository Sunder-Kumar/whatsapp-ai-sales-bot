import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from bot.session import WhatsAppSession

class MessageMonitor:
    def __init__(self, session: WhatsAppSession, redis_url: str):
        self.session = session
        self.redis_url = redis_url
        self.redis = None

    async def start(self):
        self.redis = await redis.from_url(self.redis_url)
        print("Message Monitor (Co-pilot Mode) started.")
        
        while True:
            try:
                await self.check_for_messages()
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            # Check every 10 seconds to be responsive but not heavy
            await asyncio.sleep(10)

    async def check_for_messages(self):
        page = await self.session.get_page()
        
        # 1. Find all chats (we check the top list to see if admin is active)
        # Selector for chat rows in the sidebar
        chats = await page.query_selector_all("div[role='row']")
        
        for i, chat in enumerate(chats[:10]): # Check top 10 most recent chats
            try:
                # Check for unread badge
                unread_badge = await chat.query_selector("span[aria-label*='unread']")
                
                # Get phone/name from the chat row
                # Note: This selector might need adjustment based on WhatsApp Web's latest HTML
                title_el = await chat.query_selector("span[title]")
                if not title_el:
                    continue
                
                chat_title = await title_el.get_attribute("title")
                phone = self.extract_phone(chat_title)
                
                if unread_badge:
                    # Admin hasn't read the message yet
                    first_seen = await self.redis.get(f"pending_ai_reply:{phone}")
                    
                    if not first_seen:
                        # First time seeing this unread chat, start the 5-min timer
                        await self.redis.set(f"pending_ai_reply:{phone}", datetime.now().isoformat(), ex=600)
                        print(f"Detected unread from {phone}. Starting 5-min grace period for Admin.")
                    else:
                        # Check if 5 minutes have passed
                        start_time = datetime.fromisoformat(first_seen.decode())
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed >= 60 : # 60 seconds = 1 minute
                            print(f"1 minute passed for {phone} without Admin response. AI taking over...")
                            await self.process_chat(chat, phone, chat_title)
                            await self.redis.delete(f"pending_ai_reply:{phone}")
                else:
                    # No unread badge - either admin read it or admin replied
                    # We should check if the LAST message was from the Admin
                    # If so, we clear any pending AI reply
                    await self.redis.delete(f"pending_ai_reply:{phone}")

            except Exception as e:
                # print(f"Error checking chat row {i}: {e}")
                continue

    async def process_chat(self, chat_element, phone, chat_name):
        page = await self.session.get_page()
        
        # Click the chat to load messages
        await chat_element.click()
        await asyncio.sleep(1) # Wait for chat to focus
        
        # Identify the sender and message content
        messages = await page.query_selector_all("div.message-in")
        if not messages:
            return

        last_msg = messages[-1]
        content = await last_msg.inner_text()
        
        # Determine message type
        msg_type = "text"
        if await last_msg.query_selector("span[data-icon='audio-play']"):
            msg_type = "voice_note"
        elif await last_msg.query_selector("img"):
            msg_type = "image"
        
        payload = {
            "phone": phone,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "chat_name": chat_name
        }
        
        await self.redis.lpush("incoming_queue", json.dumps(payload))
        print(f"Pushed message from {phone} to AI queue after 5-min delay.")

    def extract_phone(self, text):
        # Basic cleanup
        return text.replace(" ", "").replace("-", "").replace("+", "")

async def run_monitor():
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
