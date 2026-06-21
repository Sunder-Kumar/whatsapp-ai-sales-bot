from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Placeholder for Background Workers ---
async def message_processor():
    print("Starting Message Processor...")
    # This will be implemented in Phase 2/5
    pass

async def follow_up_checker():
    print("Starting Follow-up Checker...")
    # This will be implemented in Phase 6
    pass

async def telegram_bot_runner():
    print("Starting Telegram Bot...")
    # This will be implemented in Phase 5
    pass

from workers.follow_up_scheduler import start_scheduler as start_followup_scheduler
from workers.session_keepalive import session_keepalive
from workers.message_processor import start_processor as start_message_processor
from bot.session import WhatsAppSession
from bot.sender import MessageSender
from bot.monitor import MessageMonitor

from admin.telegram_bot import TelegramAdminBot

# Global instances
whatsapp_session = WhatsAppSession(headless=True)
message_sender = MessageSender(whatsapp_session)
telegram_admin_bot = TelegramAdminBot()
message_monitor = MessageMonitor(whatsapp_session, os.getenv("REDIS_URL", "redis://localhost:6379"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")

    # 1. Start WhatsApp Session
    await whatsapp_session.start()

    # 2. Start Session Keep-alive in background
    asyncio.create_task(session_keepalive(whatsapp_session))

    # 2b. Start WhatsApp message monitor in background
    message_monitor_task = asyncio.create_task(message_monitor.start())

    # 3. Start Follow-up Scheduler
    await start_followup_scheduler(message_sender)

    # 4. Start Message Processor
    message_processor_task = asyncio.create_task(start_message_processor(message_sender))

    # 5. Start Telegram Bot in the background if configured
    telegram_task = asyncio.create_task(telegram_admin_bot.start())
    print("Telegram Admin Bot startup task created.")

    yield

    print("Application shutting down...")
    message_monitor_task.cancel()
    message_processor_task.cancel()
    telegram_task.cancel()
    await asyncio.gather(message_monitor_task, message_processor_task, telegram_task, return_exceptions=True)
    await whatsapp_session.stop()
    try:
        await telegram_admin_bot.stop()
    except Exception as e:
        print(f"Telegram Admin Bot shutdown error: {e}")

from admin.dashboard import router as admin_router

app = FastAPI(
    title="WhatsApp AI Bot API",
    description="Backend for WhatsApp Automation with AI & Mobile Admin",
    version="1.0.0",
    lifespan=lifespan
)

# ... (middleware and templates unchanged)

# --- Routes ---

@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "message": "WhatsApp AI Bot is running",
        "version": "1.0.0"
    }

app.include_router(admin_router, prefix="/admin", tags=["Admin"])
# app.include_router(api_router, prefix="/api", tags=["API"], dependencies=[Depends(verify_admin_key)])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
