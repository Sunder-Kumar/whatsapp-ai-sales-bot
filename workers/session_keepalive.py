import asyncio
from bot.session import WhatsAppSession

async def session_keepalive(session: WhatsAppSession):
    """
    Background task to ensure the WhatsApp Web session is healthy.
    """
    print("Session Keep-alive worker started.")
    while True:
        try:
            page = await session.get_page()
            
            # Check if the main chat list is visible
            # Selector for chat list or search bar
            is_visible = await page.is_visible("div[contenteditable='true'][data-tab='3']")
            
            if not is_visible:
                print("⚠️ WhatsApp Web session appears disconnected. Refreshing...")
                await page.reload()
                await asyncio.sleep(15)
                
                # Check again after reload
                if not await page.is_visible("div[contenteditable='true'][data-tab='3']"):
                    print("🚨 ALERT: WhatsApp Web session is DOWN. Manual intervention required (scan QR).")
                    # Here you would trigger a Telegram alert
            else:
                # Optional: Simulate a small scroll or click to keep the session active
                # print("Session healthy.")
                pass
                
        except Exception as e:
            print(f"Error in keep-alive worker: {e}")
            
        # Check every 5 minutes
        await asyncio.sleep(300)
