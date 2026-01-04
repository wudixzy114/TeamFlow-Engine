# init_db.py 
import asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi.concurrency import run_in_threadpool # <--- 1. 導入 run_in_threadpool

# 1. 從異步的 database.py 導入
from app.core.database import AsyncSessionLocal
from app.core.models import User
from app.core.security import get_password_hash

async def seed_users():
    async with AsyncSessionLocal() as db:
        users_to_create = [
            {"username": "test1", "email": "test1@gmail.com", "password": "test1"},
            {"username": "test2", "email": "test2@gmail.com", "password": "test2"},
            {"username": "test3", "email": "test3@gmail.com", "password": "test3"},
        ]

        for u in users_to_create:
            query = select(User).where(User.email == u["email"])
            result = await db.execute(query)
            if not result.scalars().first():
                
                # --- 2. 在背景線程中執行緩慢的同步函式 ---
                hashed_password = await run_in_threadpool(get_password_hash, u["password"])

                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hashed_password, # 使用異步方式得到的結果
                )
                db.add(user)
                try:
                    await db.commit()
                    print(f"✅ Created user: {u['username']}")
                except IntegrityError:
                    await db.rollback()
                    print(f"⚠️  Skipped duplicate: {u['email']}")

if __name__ == "__main__":
    asyncio.run(seed_users())