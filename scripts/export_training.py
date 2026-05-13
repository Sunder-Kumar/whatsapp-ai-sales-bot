import asyncio
import json
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from db.models import Message, Conversation
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("sqlite:///", "sqlite+aiosqlite:///")

async def export_training_data():
    """
    Exports messages marked as training examples to JSON files for RAG.
    """
    print("Exporting training data from database...")
    
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Fetch conversations that were delivered (successful)
        # or manually marked for training
        result = await session.execute(
            select(Message).where(Message.is_training_example == True)
        )
        messages = result.scalars().all()

        if not messages:
            print("No messages marked as 'is_training_example' found.")
            return

        # Group by phone/conversation
        conversations = {}
        for msg in messages:
            if msg.phone not in conversations:
                conversations[msg.phone] = []
            conversations[msg.phone].append({
                "role": msg.role,
                "content": msg.content
            })

        # Save to data/mock/
        for phone, history in conversations.items():
            filename = f"exported_{phone}.json"
            folder = "whatsapp-bot/data/mock/successful" # Default to successful for now
            filepath = os.path.join(folder, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            print(f"✅ Exported conversation for {phone} to {filepath}")

if __name__ == "__main__":
    asyncio.run(export_training_data())
