# db/database.py

import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SQL_ECHO = os.getenv("SQL_ECHO", "False").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 5))

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in the environment variables.")

# Create async engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    future=True,
)

# Create sessionmaker for async sessions
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# For compatibility (if you need sync engine, e.g., for Alembic migrations)
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL.replace("+asyncpg", ""),
    echo=SQL_ECHO,
    future=True,
)

# Dependency for FastAPI routes
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Function to create tables (should be called at startup)
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
