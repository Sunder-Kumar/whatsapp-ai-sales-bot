from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import redis.asyncio as redis
import os
import yaml
from dotenv import load_dotenv

from db.models import Conversation
from admin.analytics import get_dashboard_stats, get_sales_by_package, get_daily_sales_trend

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="whatsapp-bot/admin/templates")
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Database dependency (Placeholder - should be integrated with your actual DB session logic)
async def get_db():
    # This is a placeholder. You'll need to use your actual SQLAlchemy session maker.
    pass

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Serves the main admin dashboard page.
    """
    # Load config for bot name
    with open("whatsapp-bot/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    bot_name = config.get("bot_settings", {}).get("name", "Premium Stream Bot")

    # Fetch stats (In a real app, use the db session)
    # stats = await get_dashboard_stats(db)
    # package_sales = await get_sales_by_package(db)
    # trend_sales = await get_daily_sales_trend(db)
    
    # Placeholder data for demonstration
    stats = {"total_revenue": 0, "total_sales": 0, "active_chats": 0}
    package_sales = {"Netflix": 0, "Spotify": 0}
    trend_sales = {"2026-05-13": 0}
    chats = [] # List of Conversation models

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "bot_name": bot_name,
        "stats": stats,
        "package_sales": package_sales,
        "trend_sales": trend_sales,
        "chats": chats
    })

@router.post("/takeover/{phone}")
async def activate_takeover(phone: str):
    await redis_client.set(f"paused:{phone}", "1")
    return {"status": "success"}

@router.post("/resume/{phone}")
async def deactivate_takeover(phone: str):
    await redis_client.delete(f"paused:{phone}")
    return {"status": "success"}
