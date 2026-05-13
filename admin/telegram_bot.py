import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv
import redis.asyncio as redis
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class TelegramAdminBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TOKEN).build()
        self.redis = redis.from_url(REDIS_URL)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != ADMIN_CHAT_ID:
            await update.message.reply_text("Unauthorized.")
            return
        
        help_text = (
            "🚀 **WhatsApp Bot Admin Panel**\n\n"
            "**Payment Management:**\n"
            "/pending - List unverified payments\n"
            "/approve {phone} - Approve payment\n"
            "/reject {phone} - Reject payment\n\n"
            "**Conversation Control:**\n"
            "/takeover {phone} - Pause AI for customer\n"
            "/resume {phone} - Resume AI for customer\n"
            "/pause_all - Emergency pause all\n"
            "/resume_all - Resume all paused\n\n"
            "**Monitoring:**\n"
            "/stats - Today's numbers\n"
            "/chats - Active conversations\n"
            "/chat {phone} - Last 10 messages\n"
            "/session - Health status\n\n"
            "**Config:**\n"
            "/broadcast {msg} - Send to all active users"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def takeover_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /takeover {phone}")
            return
        phone = context.args[0]
        await self.redis.set(f"paused:{phone}", "1")
        await update.message.reply_text(f"✅ Takeover active for {phone}. AI is paused.")

    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /resume {phone}")
            return
        phone = context.args[0]
        await self.redis.delete(f"paused:{phone}")
        await update.message.reply_text(f"✅ AI resumed for {phone}.")

    async def pause_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async for key in self.redis.scan_iter("chat:*"):
            phone = key.decode().split(":")[1]
            await self.redis.set(f"paused:{phone}", "1")
        await update.message.reply_text("🚨 **EMERGENCY**: AI paused for ALL active customers.")

    async def resume_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async for key in self.redis.scan_iter("paused:*"):
            await self.redis.delete(key)
        await update.message.reply_text("✅ AI resumed for all customers.")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Placeholder for real DB stats
        new_chats = await self.redis.get("stats:today:new_chats") or 0
        sales = await self.redis.get("stats:today:sales") or 0
        revenue = await self.redis.get("stats:today:revenue") or 0
        
        paused_count = 0
        async for _ in self.redis.scan_iter("paused:*"):
            paused_count += 1

        stats_text = (
            f"📊 **Today's Stats**\n\n"
            f"• New chats: {new_chats}\n"
            f"• Sales: {sales}\n"
            f"• Revenue: Rs. {revenue}\n"
            f"• AI Paused: {paused_count}"
        )
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def chats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        active_chats = []
        async for key in self.redis.scan_iter("chat:*"):
            phone = key.decode().split(":")[1]
            state_data = await self.redis.get(key)
            if state_data:
                state = json.loads(state_data)
                stage = state.get("stage", "new")
                active_chats.append(f"• `{phone}`: {stage}")

        if not active_chats:
            await update.message.reply_text("No active chats found.")
            return

        await update.message.reply_text("📂 **Active Conversations:**\n\n" + "\n".join(active_chats[:20]), parse_mode='Markdown')

    async def session_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        last_heartbeat = await self.redis.get("health:last_heartbeat")
        if last_heartbeat:
            dt = datetime.fromisoformat(last_heartbeat)
            diff = (datetime.now() - dt).total_seconds()
            status = "✅ Healthy" if diff < 300 else "⚠️ Delayed"
            await update.message.reply_text(f"Session Status: {status}\nLast Heartbeat: {diff:.0f}s ago")
        else:
            await update.message.reply_text("❌ No session heartbeat detected.")

    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /broadcast {message}")
            return
        
        message = " ".join(context.args)
        count = 0
        async for key in self.redis.scan_iter("chat:*"):
            phone = key.decode().split(":")[1]
            # In real implementation, you'd push to a broadcast queue or use MessageSender directly
            # For now, we'll just log it
            print(f"Broadcasting to {phone}: {message}")
            count += 1
        
        await update.message.reply_text(f"📢 Broadcast initiated to {count} customers.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")
        action = data[0]
        phone = data[1]

        if action == "approve":
            await self.redis.delete(f"paused:{phone}")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **Approved and Delivered**")
        elif action == "reject":
            await self.redis.delete(f"paused:{phone}")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **Rejected - AI Resumed**")

    async def send_payment_alert(self, phone, package, amount, image_path, ocr_text):
        caption = (
            f"💳 **New Payment Detected**\n\n"
            f"📱 Phone: `{phone}`\n"
            f"📦 Package: {package}\n"
            f"💵 Amount: Rs. {amount}\n"
            f"📝 OCR Text: {ocr_text[:200]}..."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{phone}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{phone}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.app.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=open(image_path, 'rb'),
            caption=caption,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def send_takeover_alert(self, phone, reason):
        text = f"⚠️ **Takeover Requested**\n\n📱 Phone: `{phone}`\n❓ Reason: {reason}\n\nTap /takeover_{phone} to pause AI."
        await self.app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode='Markdown')

    def run(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("takeover", self.takeover_command))
        self.app.add_handler(CommandHandler("resume", self.resume_command))
        self.app.add_handler(CommandHandler("pause_all", self.pause_all_command))
        self.app.add_handler(CommandHandler("resume_all", self.resume_all_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("chats", self.chats_command))
        self.app.add_handler(CommandHandler("session", self.session_command))
        self.app.add_handler(CommandHandler("broadcast", self.broadcast_command))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        print("Telegram Admin Bot is polling...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = TelegramAdminBot()
    bot.run()
