from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import redis.asyncio as redis
import os
import yaml
import html
from dotenv import load_dotenv

from db.models import Conversation
from admin.analytics import get_dashboard_stats, get_sales_by_package, get_daily_sales_trend

load_dotenv()

router = APIRouter()
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))

# Database dependency (Placeholder - should be integrated with your actual DB session logic)
async def get_db():
    # This is a placeholder. You'll need to use your actual SQLAlchemy session maker.
    pass

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Serves the main admin dashboard page.
    """
    config = load_config()
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

@router.get("/config", response_class=HTMLResponse)
async def admin_config():
    config = load_config()
    bot_name = config.get("bot_settings", {}).get("name", "Premium Stream Bot")
    config_yaml = html.escape(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))

    return HTMLResponse(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(bot_name)} Config</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <nav class="bg-indigo-600 text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">{html.escape(bot_name)} Config</h1>
            <a href="/admin/" class="hover:underline">← Dashboard</a>
        </div>
    </nav>
    <main class="container mx-auto p-6">
        <section class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-lg font-bold mb-4">Current config.yaml</h2>
            <pre class="bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto text-sm">{config_yaml}</pre>
        </section>
    </main>
</body>
</html>
""")

@router.post("/takeover/{phone}")
async def activate_takeover(phone: str):
    await redis_client.set(f"paused:{phone}", "1")
    return {"status": "success"}

@router.post("/resume/{phone}")
async def deactivate_takeover(phone: str):
    await redis_client.delete(f"paused:{phone}")
    return {"status": "success"}
