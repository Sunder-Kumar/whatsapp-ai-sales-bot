# 📱 Telegram Mobile Admin Guide

This guide explains how to set up, verify, and use the Telegram Bot to manage your WhatsApp AI Sales Bot from your phone.

---

## 🛠 1. Setup Instructions

To use the mobile admin, you must first create your own Telegram bot and link it to your project.

### **Step A: Create the Bot**
1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot`.
3. Follow the instructions to give your bot a name and a username.
4. Copy the **API Token** provided by BotFather.
5. Paste it into your `.env` file: `TELEGRAM_BOT_TOKEN=your_token_here`

### **Step B: Get Your Chat ID**
1. Search for **@userinfobot** on Telegram.
2. Send any message to it.
3. It will reply with your **Id** (a series of numbers).
4. Paste it into your `.env` file: `TELEGRAM_ADMIN_CHAT_ID=your_id_here`

### **Step C: Start the Bot**
1. Open your newly created bot on Telegram.
2. Tap the **Start** button or send `/start`.

---

## 🔐 2. Bot Verification
To verify the bot is correctly connected to your WhatsApp system:
1. Run your bot: `uvicorn main:app`.
2. Send `/session` to the bot on Telegram.
3. If it returns **"Healthy"** or **"Delayed"**, the connection is verified.
4. If it says **"Unauthorized"**, ensure your `TELEGRAM_ADMIN_CHAT_ID` in `.env` matches your ID.

---

## 📜 3. Command Reference

The bot supports the following commands for full remote management:

### **General Commands**
- `/start` - Initializes the admin session and shows the main menu.
- `/help` - **List all available commands and their functions (detailed below).**
- `/stats` - View today's performance (New chats, Sales made, Total Revenue).
- `/session` - Check if the WhatsApp Web connection is alive and healthy.

### **Payment Management**
- `/pending` - Lists all customers who have sent a screenshot but are not yet verified.
- `/approve {phone}` - Verifies a payment and **automatically delivers** the login credentials.
- `/reject {phone}` - Rejects a payment, resumes the AI, and asks the customer for a correct screenshot.

### **Conversation & AI Control**
- `/chats` - Shows a list of the 20 most recent active conversations and their current sales stage.
- `/chat {phone}` - Retrieves the last 10 messages of a specific conversation for review.
- `/takeover {phone}` - **Pauses the AI** for that specific customer so you can chat manually.
- `/resume {phone}` - Unpauses the AI and allows it to continue the sales flow.
- `/pause_all` - **Emergency Stop**: Pauses the AI for every active customer at once.
- `/resume_all` - Resumes the AI for everyone who was previously paused.

### **Marketing & Config**
- `/broadcast {message}` - Sends a one-time message to every active customer (useful for offers or downtime notices).

---

## 🆘 4. The /help Command
The `/help` command is your main reference inside Telegram. It provides a quick-access list of functions:

> **Admin Functions:**
> - **Payments**: Approve/Reject receipts with one tap.
> - **Takeover**: Pause AI to handle difficult customers yourself.
> - **Broadcast**: Send bulk updates to your active leads.
> - **Health**: Monitor if your server or WhatsApp session is down.
> - **Stats**: Track your daily profit and conversion rates.

---

## 🔔 5. Automatic Alerts (No Command Needed)
The bot will proactively message you when the following events occur:
1. **📱 New Customer**: Alerts you when a new person starts a chat.
2. **💳 Payment Detected**: Sends the screenshot + OCR text + Approve/Reject buttons instantly.
3. **⚠️ Human Requested**: Notifies you if the customer asks for a "manager" or "owner".
4. **❌ Session Dropped**: Emergency alert if WhatsApp Web logs out on the server.
5. **📊 Daily Summary**: A full report sent to you every night at 11:00 PM.

---

**Note:** Always keep your `TELEGRAM_BOT_TOKEN` private. Anyone with access to your Telegram bot can control your business and view customer data.
