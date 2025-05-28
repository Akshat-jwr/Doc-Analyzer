import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "document_intelligence")

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(MONGODB_URL)
        db.database = db.client[DATABASE_NAME]
        
        # Import all models for Beanie initialization
        from models.user import User
        from models.pdf import PDF
        from models.page_text import PageText
        from models.table import Table
        from models.image import Image
        from models.chat_session import ChatSession
        from models.chat_message import ChatMessage
        from auth.models import OTP
        
        # Initialize Beanie
        await init_beanie(
            database=db.database,
            document_models=[
                User, PDF, PageText, Table, Image, 
                ChatSession, ChatMessage, OTP
            ]
        )
        
        logger.info(f"Connected to MongoDB: {DATABASE_NAME}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def get_database():
    """Get database instance"""
    return db.database

# Health check
async def check_database_health():
    """Check MongoDB connection health"""
    try:
        await db.client.admin.command('ismaster')
        return {
            "status": "healthy",
            "database": "connected",
            "db_name": DATABASE_NAME
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }
