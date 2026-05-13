import asyncio
import redis.asyncio as redis
import os
import json
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.sender import MessageSender
from ai.prompt_builder import PromptBuilder
from ai.llm import ai_engine
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class FollowUpManager:
    def __init__(self, sender: MessageSender):
        self.sender = sender
        self.redis = redis.from_url(REDIS_URL)
        self.prompt_builder = PromptBuilder()

    async def check_followups(self):
        """
        Main loop to check for pending follow-ups.
        Actually, we use Redis TTL to detect when a customer is silent.
        But for this implementation, we'll scan Redis keys.
        """
        print("Checking for follow-ups...")
        # Get all chat states
        async for key in self.redis.scan_iter("chat:*"):
            phone = key.decode().split(":")[1]
            
            # Check if customer is paused or already converted/lost
            state_data = await self.redis.get(key)
            if not state_data:
                continue
            
            state = json.loads(state_data)
            stage = state.get("stage", "new")
            
            # Skip if state is not eligible for follow-ups
            if stage in ["payment_pending", "manual_verification", "delivered", "closed_won", "closed_lost"]:
                continue
            
            # Check if AI is paused manually
            is_paused = await self.redis.exists(f"paused:{phone}")
            if is_paused:
                continue

            # Check last message time
            last_msg_time_str = state.get("last_message_at")
            if not last_msg_time_str:
                continue
            
            last_msg_time = datetime.fromisoformat(last_msg_time_str)
            seconds_since_last = (datetime.now() - last_msg_time).total_seconds()
            
            followup_count = int(await self.redis.get(f"followup_count:{phone}") or 0)
            
            # 1 Hour Follow-up
            if followup_count == 0 and seconds_since_last >= 3600:
                await self.send_followup(phone, state, 1)
            
            # 6 Hours Follow-up
            elif followup_count == 1 and seconds_since_last >= 21600:
                await self.send_followup(phone, state, 2)
            
            # 24 Hours Follow-up
            elif followup_count == 2 and seconds_since_last >= 86400:
                await self.send_followup(phone, state, 3)
            
            # 48 Hours - Mark as Lost
            elif followup_count == 3 and seconds_since_last >= 172800:
                state["stage"] = "closed_lost"
                await self.redis.set(f"chat:{phone}", json.dumps(state))
                print(f"Customer {phone} marked as closed_lost.")

    async def send_followup(self, phone, state, sequence_num):
        """
        Generates and sends a follow-up message using the AI.
        """
        print(f"Sending follow-up {sequence_num} to {phone}...")
        
        # We can either use pre-defined templates or let AI generate one
        followup_prompts = {
            1: "Customer is silent for 1 hour. Ask if they are still interested or have questions in a friendly way.",
            2: "Customer silent for 6 hours. Mention that the offer for {package} is great and they should take it now.",
            3: "Customer silent for 24 hours. Final follow-up. Mention prices might update soon. Be helpful but urgent."
        }
        
        package = state.get("selected_package", "premium accounts")
        prompt_text = followup_prompts[sequence_num].format(package=package)
        
        system_prompt = self.prompt_builder.build_system_prompt(state)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"INSTRUCTION: {prompt_text}"}
        ]
        
        reply = await ai_engine.generate_reply(messages)
        success = await self.sender.send_text(phone, reply)
        
        if success:
            await self.redis.incr(f"followup_count:{phone}")
            # Update last message time so we don't spam
            state["last_message_at"] = datetime.now().isoformat()
            await self.redis.set(f"chat:{phone}", json.dumps(state))

async def start_scheduler(sender: MessageSender):
    manager = FollowUpManager(sender)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(manager.check_followups, 'interval', minutes=10)
    scheduler.start()
    print("Follow-up Scheduler started.")
    return scheduler
