import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import connect_to_mongo, close_mongo_connection
from endpoints import auth_router, health_router, tables_router
from endpoints.pdf import router as pdf_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Document Intelligence API",
    description="API for document processing and analysis with AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up and connecting to MongoDB...")
    try:
        await connect_to_mongo()
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    logger.info("Shutting down and closing MongoDB connection...")
    await close_mongo_connection()

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(pdf_router)
app.include_router(tables_router)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Document Intelligence API is running with MongoDB!",
        "version": "1.0.0",
        "database": "MongoDB",
        "docs": "/docs"
    }
