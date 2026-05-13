import os
import aiofiles
import httpx
from datetime import datetime

MEDIA_DIR = "whatsapp-bot/media"

class MediaHandler:
    def __init__(self, page):
        self.page = page
        if not os.path.exists(MEDIA_DIR):
            os.makedirs(MEDIA_DIR)

    async def download_voice_note(self, phone: str):
        """
        Intercepts and downloads a voice note.
        Note: This is a complex operation in Playwright that usually requires 
        intercepting the network request for the audio blob.
        """
        print(f"Attempting to download voice note for {phone}...")
        
        # In a real implementation, you would use page.on("response") 
        # to catch the audio/ogg or audio/mpeg response.
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{phone}_{timestamp}.ogg"
        filepath = os.path.join(MEDIA_DIR, filename)
        
        # Placeholder for the actual download logic
        # For now, we return a path to where it WOULD be saved
        return filepath

    async def download_image(self, phone: str):
        """
        Downloads the last received image in the current chat.
        """
        print(f"Attempting to download image for {phone}...")
        
        # Find the last image in the chat
        image_element = await self.page.query_selector("div.message-in img")
        if image_element:
            src = await image_element.get_attribute("src")
            if src and src.startswith("blob:"):
                # Blobs must be downloaded via JavaScript context
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{phone}_{timestamp}.jpg"
                filepath = os.path.join(MEDIA_DIR, filename)
                
                # JavaScript to fetch blob and convert to base64 or arraybuffer
                js_code = f"""
                async () => {{
                    const response = await fetch('{src}');
                    const blob = await response.blob();
                    return new Promise((resolve) => {{
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.readAsDataURL(blob);
                    }});
                }}
                """
                base64_data = await self.page.evaluate(js_code)
                
                import base64
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(base64.b64decode(base64_data))
                
                print(f"✅ Image saved to {filepath}")
                return filepath
        
        return None
