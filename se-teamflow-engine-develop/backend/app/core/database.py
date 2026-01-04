from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base # declarative_base 現在建議從 orm 導入
from sqlalchemy.orm import sessionmaker
from .config import settings

# 假設您的 DATABASE_URL 是 "postgresql://..."
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False,
    pool_size=42,           # 增加連接池 (原本 40 -> 100，配合 Postgres max_connections)
    max_overflow=5,         # 允許溢出的連接數
    pool_timeout=8,
    pool_recycle=1800,
    pool_pre_ping=True,     
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()