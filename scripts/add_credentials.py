import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Credential
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("sqlite:///", "sqlite+aiosqlite:///")

async def add_credential():
    print("--- Add New Login Credential ---")
    package_name = input("Package Name (e.g., netflix_premium): ")
    email = input("Login Email: ")
    password = input("Login Password: ")
    pin = input("Profile PIN (optional, press enter to skip): ")
    notes = input("Additional Setup Notes (optional): ")

    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        new_cred = Credential(
            package_name=package_name,
            login_email=email,
            login_password=password,
            profile_pin=pin if pin else None,
            notes=notes if notes else None
        )
        session.add(new_cred)
        await session.commit()
        print(f"✅ Successfully added {email} for {package_name}")

if __name__ == "__main__":
    asyncio.run(add_credential())
