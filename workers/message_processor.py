import asyncio
import json
import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from ai.llm import ai_engine
from ai.language_detect import detect_language, should_takeover
from ai.prompt_builder import PromptBuilder
from ai.rag import rag_manager
from ai.ocr import is_payment_receipt, is_payment_intent_text
from bot.sender import MessageSender
from db.models import Customer, Conversation, Message, Order, PaymentEvent
from db.queries import update_conversation_stage, update_order_status
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create async engine for database
engine = create_async_engine(DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"))
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class MessageProcessor:
    def __init__(self, sender: MessageSender):
        self.sender = sender
        self.redis = redis.from_url(REDIS_URL)
        self.prompt_builder = PromptBuilder()

    async def _wait_for_redis(self):
        while True:
            try:
                await self.redis.ping()
                return
            except Exception as e:
                print(f"Redis connection unavailable: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def start(self):
        print("Message Processor started. Listening for messages...")
        await self._wait_for_redis()

        while True:
            try:
                # BRPOP blocks until a message is available in the queue
                msg = await self.redis.brpop("incoming_queue", timeout=5)
                if msg:
                    # msg is a tuple (queue_name, data)
                    payload = json.loads(msg[1].decode())
                    print(f"Received queued message for {payload.get('phone')}: {payload.get('type')}")
                    asyncio.create_task(self.process_message(payload))
            except RedisConnectionError as e:
                print(f"Redis connection error in message processor: {e}. Reconnecting...")
                await self._wait_for_redis()
            except asyncio.CancelledError:
                print("Message processor cancelled.")
                raise
            except Exception as e:
                print(f"Unexpected error in message processor loop: {e}")
                await asyncio.sleep(5)

    async def process_message(self, payload):
        phone = payload["phone"]
        msg_type = payload["type"]
        content = payload["content"]
        
        # 1. Check for Redis lock (prevent double processing)
        lock_key = f"lock:{phone}"
        if await self.redis.exists(lock_key):
            # Re-queue if locked
            await self.redis.lpush("incoming_queue", json.dumps(payload))
            return
        
        await self.redis.set(lock_key, "1", ex=10) # 10s lock

        try:
            # 2. Check for manual takeover/pause
            if await self.redis.exists(f"paused:{phone}"):
                print(f"Skipping {phone} - AI is paused.")
                return

            # 3. Handle Takeover Triggers
            if should_takeover(content):
                await self.redis.set(f"paused:{phone}", "1")
                # Trigger alert via Telegram (you'd normally call the bot instance here)
                print(f"ALERT: Takeover triggered for {phone}")
                return

            # 4. Get/Initialize State
            state_key = f"chat:{phone}"
            state_data = await self.redis.get(state_key)
            if state_data:
                state = json.loads(state_data)
            else:
                state = {
                    "phone": phone,
                    "stage": "new",
                    "language": "mixed",
                    "selected_package": None,
                    "last_message_at": datetime.now().isoformat()
                }

            # 5. Detect Language
            if state["stage"] == "new":
                state["language"] = detect_language(content)

            # 6. State Machine Transitions (Simplified)
            current_stage = state["stage"]
            
            # Intent detection
            buying_intent = any(kw in content.lower() for kw in ["chahiye", "price", "interested", "lena", "rate"])
            objection = any(kw in content.lower() for kw in ["mahanga", "zyada", "expensive", "discount"])
            agreement = any(kw in content.lower() for kw in ["theek hai", "okay", "le leta hun", "kaise payment"])
            
            if current_stage == "new" or current_stage == "greeted":
                if buying_intent:
                    state["stage"] = "needs_assessment"
            elif current_stage == "needs_assessment":
                # Logic to check if all info collected would go here
                # For now, let AI handle the flow until it reaches pkg_recommend
                pass
            
            # 7. Check for Payment (OCR)
            if msg_type == "image":
                # In real use, you'd download the image from media_path
                is_receipt, ocr_text = is_payment_receipt(payload.get("media_path", ""))
                if is_receipt:
                    state["stage"] = "payment_pending"
                    await self.redis.set(f"paused:{phone}", "1")
                    # Send alert to Telegram...
                    await self.sender.send_text(phone, "Sir screenshot mila, verify ho raha hai. Shukria!")
                    await self.redis.set(state_key, json.dumps(state))
                    return

            # 8. RAG Retrieval
            rag_examples = rag_manager.query_similar_conversations(content)

            # 9. AI Generation
            system_prompt = self.prompt_builder.build_system_prompt(state)
            # Mock history (last 10 messages should be loaded from DB/Redis)
            history = [{"role": "user", "content": content}]
            
            full_prompt = self.prompt_builder.build_full_prompt(system_prompt, history, rag_examples)
            reply = await ai_engine.generate_reply(full_prompt)

            # 10. Send Reply
            await self.sender.send_text(phone, reply)
            print(f"AI reply sent to {phone}.")

            # 11. Update State
            state["last_message_at"] = datetime.now().isoformat()
            await self.redis.set(state_key, json.dumps(state))
            # Reset follow-up count on new activity
            await self.redis.delete(f"followup_count:{phone}")

        except Exception as e:
            print(f"Error processing message for {phone}: {e}")
        finally:
            await self.redis.delete(lock_key)

async def start_processor(sender: MessageSender):
    processor = MessageProcessor(sender)
    while True:
        try:
            await processor.start()
        except asyncio.CancelledError:
            print("Message processor task cancelled.")
            return
        except Exception as e:
            print(f"Message processor crashed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
