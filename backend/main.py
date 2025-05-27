import logging
from fastapi import FastAPI, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from db.database import create_db_and_tables, get_session

# CRITICAL: Import all models so SQLModel knows about them
from models.user import User
from models.pdf import PDF
from models.page_text import PageText
from models.table import Table
from models.image import Image
from models.chat_session import ChatSession
from models.chat_message import ChatMessage

app = FastAPI(title="Document Intelligence API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def on_startup():
    logger.info("Starting up and initializing the database...")
    try:
        await create_db_and_tables()
        logger.info("Database tables created and ready!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@app.get("/health", tags=["Health"])
async def health_check(session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(text("SELECT 1"))
        _ = result.scalar()
        return {"status": "ok", "db": "connected"}
    except SQLAlchemyError as e:
        logger.error(f"Health check DB error: {e}")
        return {"status": "error", "db": "disconnected", "detail": str(e)}

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Your Document Intelligence API is running!"}

@app.get("/tables", tags=["Debug"])
async def list_tables(session: AsyncSession = Depends(get_session)):
    """Debug endpoint to see what tables exist"""
    try:
        result = await session.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        return {"tables": tables}
    except SQLAlchemyError as e:
        return {"error": str(e)}
