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
            selectors = [
                "#pane-side",
                "div[contenteditable='true'][data-tab='3']",
                "div[contenteditable='true'][data-tab='10']",
                "div[title='Search or start new chat']",
                "div[aria-label='Search or start new chat']"
            ]

            is_visible = False
            for selector in selectors:
                try:
                    if await page.is_visible(selector):
                        is_visible = True
                        break
                except Exception:
                    continue

            if not is_visible:
                print("⚠️ WhatsApp Web session appears disconnected. Refreshing...")
                await page.reload()
                await asyncio.sleep(15)
                
                # Check again after reload
                recovered = False
                for selector in selectors:
                    try:
                        if await page.is_visible(selector):
                            recovered = True
                            break
                    except Exception:
                        continue
                if not recovered:
                    print("🚨 ALERT: WhatsApp Web session is DOWN. Manual intervention required (scan QR).")
            else:
                pass
                
        except Exception as e:
            print(f"Error in keep-alive worker: {e}")
            
        # Check every 5 minutes
        await asyncio.sleep(300)
