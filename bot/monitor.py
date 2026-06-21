import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from bot.session import WhatsAppSession

ADMIN_GRACE_SECONDS = 10
PENDING_REPLY_TTL_SECONDS = 20


class MessageMonitor:
    def __init__(self, session: WhatsAppSession, redis_url: str):
        self.session = session
        self.redis_url = redis_url
        self.redis = None
        self.active_chat_phone = None
        self.active_chat_name = None

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
        await self.check_active_chat_for_messages(page)

        # 1. Find all chats (we check the top list to see if admin is active)
        # Selector for chat rows in the sidebar
        chats = await page.query_selector_all("div[role='row']")

        for i, chat in enumerate(chats[:10]):  # Check top 10 most recent chats
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
                        # First time seeing this unread chat, start the 2-min timer
                        await self.redis.set(
                            f"pending_ai_reply:{phone}",
                            datetime.now().isoformat(),
                            ex=PENDING_REPLY_TTL_SECONDS
                        )
                        print(f"Detected unread from {phone}. Starting {ADMIN_GRACE_SECONDS}s grace period for Admin.")
                    else:
                        # Check if the admin grace period has passed
                        start_time = datetime.fromisoformat(first_seen.decode())
                        elapsed = (datetime.now() - start_time).total_seconds()

                        if elapsed >= ADMIN_GRACE_SECONDS:
                            print(f"Admin grace period passed for {phone}. AI taking over...")
                            await self.process_chat(chat, phone, chat_title)
                            await self.redis.delete(f"pending_ai_reply:{phone}")
                else:
                    if phone == self.active_chat_phone:
                        continue

                    # No unread badge - either admin read it or admin replied
                    # We should check if the LAST message was from the Admin
                    # If so, we clear any pending AI reply
                    await self.redis.delete(f"pending_ai_reply:{phone}")

            except Exception as e:
                print(f"Error checking chat row {i}: {repr(e)}")
                continue

    async def process_chat(self, chat_element, phone, chat_name):
        page = await self.session.get_page()

        # Click the chat to load messages
        await chat_element.click()
        await asyncio.sleep(2)  # Wait for chat to focus and messages to render
        self.active_chat_phone = phone
        self.active_chat_name = chat_name

        # Baseline the message count the moment we open this chat, so
        # check_active_chat_for_messages doesn't immediately re-trigger
        # on the very message we're about to queue below.
        current_count = await self.get_chat_message_count(page)
        await self.redis.set(f"last_message_count:{phone}", current_count)

        message_data = await self.get_latest_incoming_message(page)
        if not message_data:
            await self.log_message_selector_counts(page, phone)
            return

        await self.queue_incoming_message(page, phone, chat_name, message_data)

    async def check_active_chat_for_messages(self, page):
        if not self.active_chat_phone:
            return

        phone = self.active_chat_phone
        chat_name = self.active_chat_name or phone

        # --- Verify the chat actually on-screen still matches what we think
        # is "active". If the admin (sharing this same WhatsApp Web session)
        # switched to a different conversation, our tracked phone is stale
        # and we must not keep reading/acting on the wrong chat. ---
        open_chat_title = await self.get_open_chat_title(page)
        if open_chat_title:
            open_phone = self.extract_phone(open_chat_title)
            if open_phone != phone:
                print(
                    f"Active chat changed externally (was {phone}, now {open_phone}). "
                    f"Clearing tracked active chat."
                )
                self.active_chat_phone = None
                self.active_chat_name = None
                return

        # --- Detect novelty by DOM message count, not by text/metadata
        # signature. A signature match can be wrong: identical short replies
        # ("ok", "yes"), minute-granularity timestamps, or media messages
        # with empty inner_text() can all collide with an already-processed
        # message and cause a real new message to be silently ignored. A
        # growing bubble count can't lie the same way. ---
        current_count = await self.get_chat_message_count(page)
        last_count_raw = await self.redis.get(f"last_message_count:{phone}")
        last_count = int(last_count_raw) if last_count_raw else None

        if last_count is None:
            # First time watching this chat in this session - just baseline it.
            await self.redis.set(f"last_message_count:{phone}", current_count)
            return

        if current_count <= last_count:
            # No new bubble appeared - nothing to do.
            return

        # A new message bubble appeared. Update the baseline immediately so
        # we don't re-trigger on this same bubble next poll, regardless of
        # what we do with it below.
        await self.redis.set(f"last_message_count:{phone}", current_count)

        latest_message = await self.get_latest_chat_message(page)
        if not latest_message:
            return

        if latest_message["direction"] == "outgoing":
            # Admin (or our own AI reply) sent something - clear any pending timer.
            await self.redis.delete(f"pending_ai_reply:{phone}")
            return

        if latest_message["direction"] != "incoming":
            return

        first_seen = await self.redis.get(f"pending_ai_reply:{phone}")
        if not first_seen:
            await self.redis.set(
                f"pending_ai_reply:{phone}",
                datetime.now().isoformat(),
                ex=PENDING_REPLY_TTL_SECONDS
            )
            print(f"Detected new message in open chat from {phone}. Starting admin grace period.")
            return

        start_time = datetime.fromisoformat(first_seen.decode())
        elapsed = (datetime.now() - start_time).total_seconds()

        if elapsed >= ADMIN_GRACE_SECONDS:
            print(f"Admin grace period passed for open chat {phone}. AI taking over...")
            await self.queue_incoming_message(page, phone, chat_name, latest_message)
            await self.redis.delete(f"pending_ai_reply:{phone}")

    async def queue_incoming_message(self, page, phone, chat_name, message_data):
        last_msg = message_data["element"]
        content = message_data["content"]
        signature = self.message_signature(message_data)

        processed_signature = await self.redis.get(f"last_processed_incoming:{phone}")
        if processed_signature and processed_signature.decode() == signature:
            print(f"Skipping already processed incoming message for {phone}.")
            return

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
        await self.redis.set(f"last_processed_incoming:{phone}", signature, ex=86400)
        print(f"Pushed message from {phone} ({chat_name}) to AI queue after admin grace period.")

    async def get_chat_message_count(self, page):
        """Count of message bubbles currently rendered in the open chat.
        Used purely as a 'did something new arrive' signal - robust to
        duplicate text and media-only messages, unlike content signatures.
        """
        try:
            elements = await page.query_selector_all(
                "div.message-in, div[class*='message-in'], "
                "div.message-out, div[class*='message-out']"
            )
            return len(elements)
        except Exception as e:
            print(f"Failed to count chat messages: {repr(e)}")
            return 0

    async def get_open_chat_title(self, page):
        """Reads the contact/group name from the header of whichever chat
        is currently displayed, so we can verify it matches active_chat_phone.
        """
        try:
            header = await page.query_selector("header")
            if not header:
                return None
            title_el = await header.query_selector("span[title]")
            if not title_el:
                return None
            return await title_el.get_attribute("title")
        except Exception as e:
            print(f"Failed to read open chat title: {repr(e)}")
            return None

    async def get_latest_chat_message(self, page):
        selector = (
            "div.message-in, "
            "div[class*='message-in'], "
            "div.message-out, "
            "div[class*='message-out']"
        )

        try:
            elements = await page.query_selector_all(selector)
            for element in reversed(elements):
                class_name = await element.get_attribute("class") or ""
                direction = "unknown"
                if "message-in" in class_name:
                    direction = "incoming"
                elif "message-out" in class_name:
                    direction = "outgoing"

                content = (await element.inner_text()).strip()
                if not content:
                    # Media-only message (image/voice/sticker) - don't skip
                    # past it to an older bubble, that's how new messages
                    # used to get silently swallowed. Use a placeholder.
                    if await element.query_selector("span[data-icon='audio-play']"):
                        content = "[voice note]"
                    elif await element.query_selector("img"):
                        content = "[image]"
                    else:
                        content = "[media]"

                return {
                    "element": element,
                    "content": content,
                    "direction": direction,
                    "metadata": await self.get_message_metadata(element),
                }
        except Exception as e:
            print(f"Latest message selector failed: {repr(e)}")

        return None

    async def get_latest_incoming_message(self, page):
        selectors = [
            "div.message-in",
            "div[class*='message-in']",
            "div[role='row']:has(div[data-pre-plain-text])",
            "div[data-pre-plain-text]",
            "span.selectable-text",
        ]

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in reversed(elements):
                    content = (await element.inner_text()).strip()
                    if content:
                        return {
                            "element": element,
                            "content": content,
                            "direction": "incoming",
                            "metadata": await self.get_message_metadata(element),
                        }
            except Exception as e:
                print(f"Message selector failed ({selector}): {repr(e)}")

        return None

    async def get_message_metadata(self, element):
        try:
            metadata = await element.get_attribute("data-pre-plain-text")
            if metadata:
                return metadata

            metadata_el = await element.query_selector("[data-pre-plain-text]")
            if metadata_el:
                return await metadata_el.get_attribute("data-pre-plain-text") or ""
        except Exception:
            pass

        return ""

    def message_signature(self, message_data):
        return f"{message_data.get('metadata', '')}|{message_data.get('content', '')}"

    async def log_message_selector_counts(self, page, phone):
        selectors = [
            "div.message-in",
            "div[class*='message-in']",
            "div.message-out",
            "div[class*='message-out']",
            "div[data-pre-plain-text]",
            "span.selectable-text",
            "div[role='row']",
        ]

        counts = {}
        for selector in selectors:
            try:
                counts[selector] = len(await page.query_selector_all(selector))
            except Exception as e:
                counts[selector] = f"error: {repr(e)}"

        print(f"No readable incoming message found for {phone}. Selector counts: {counts}")

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