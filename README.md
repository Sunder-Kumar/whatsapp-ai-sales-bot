# 🚀 WhatsApp AI Sales Bot (Always-On)

A professional-grade, autonomous WhatsApp Sales Bot designed to run 24/7 on a cloud server. It handles everything from customer inquiries in Roman Urdu/English to payment verification and automated service delivery.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright)](https://playwright.dev/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3-f34f29?style=for-the-badge)](https://groq.com/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

---

## ✨ Key Features

- **🤖 Autonomous AI Sales**: Uses Groq (Llama 3.3 70B) for lightning-fast, human-like sales conversations.
- **🎙️ Voice Note Transcription**: Local Whisper-based STT (no API cost).
- **📸 Automated OCR**: Detects and reads payment receipts using Tesseract.
- **📱 Mobile Admin Control**: Manage everything via a dedicated Telegram Bot (Approve payments, Take over chats, View stats).
- **🖥️ Web Dashboard**: Real-time analytics, revenue tracking, and live chat monitoring.
- **🧠 RAG (Retrieval-Augmented Generation)**: Learns from your past successful sales conversations using ChromaDB.
- **⏳ Smart Follow-Ups**: Automated 1h, 6h, and 24h follow-up sequences to recover leads.
- **🔒 Human-Like Behavior**: Simulated typing, reading delays, and automatic frustration detection.

---

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Automation**: Playwright (WhatsApp Web)
- **Database**: SQLAlchemy (SQLite/PostgreSQL) + Redis (State Management)
- **AI/ML**: Groq API, OpenAI Whisper (Local), Tesseract OCR, ChromaDB
- **Process Management**: PM2

---

## 📂 Project Structure

```text
whatsapp-bot/
├── admin/          # Dashboard & Telegram Bot logic
├── ai/             # LLM, Whisper, OCR, & RAG components
├── bot/            # WhatsApp automation (Playwright)
├── db/             # Models & Database queries
├── workers/        # Background jobs (Follow-ups, Keep-alive)
├── scripts/        # Utility scripts (RAG builder, Credential manager)
├── data/mock/      # Training data for RAG
├── templates/      # Message & Email templates
└── main.py         # Entry point
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Redis Server
- Tesseract OCR & FFmpeg
- A Groq API Key (Free)
- A Telegram Bot Token (via @BotFather)

### 2. Installation
```bash
git clone https://github.com/yourusername/whatsapp-bot.git
cd whatsapp-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Configuration
Copy the `.env` template and fill in your keys:
```bash
cp .env.example .env  # Manual copy if .env.example exists
```

### 4. Initialization
```bash
# Scan WhatsApp QR Code (Run once)
python bot/scanner.py

# Build AI Memory (RAG)
python scripts/build_rag.py

# Run the Bot
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🛡️ Security & Safety

- **Session Protection**: The `session/` folder contains your active WhatsApp login. **Never share it.**
- **Anti-Ban**: This bot uses randomized delays. Using it for bulk spam will result in a ban.
- **Environment**: Keep your `.env` out of source control (added to `.gitignore`).

---

## 📊 Monitoring

- **Web UI**: `http://localhost:8000/admin`
- **Telegram**: Instant alerts for payments and takeover requests.

---

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
