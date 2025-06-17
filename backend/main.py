import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import connect_to_mongo, close_mongo_connection
from endpoints import auth_router, health_router, tables_router
from endpoints.pdf import router as pdf_router
from endpoints.multi_chat import router as multi_chat_router  # ✅ ADD THIS
from endpoints.llm_visualization import router as visualization_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Document Intelligence API with AI Chat",
    description="API for document processing and analysis with AI chatbot capabilities",
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
    """Initialize database and chatbot on startup"""
    logger.info("Starting up and connecting to MongoDB...")
    try:
        await connect_to_mongo()
        logger.info("Successfully connected to MongoDB!")
        
        # Initialize chatbot service
        # from backend.services.multi_chat_service import general_chatbot_service
        # logger.info("✅ General Chatbot Service ready!")
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
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
app.include_router(multi_chat_router)  # ✅ ADD THIS
app.include_router(visualization_router)  # ✅ ADD THIS

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Document Intelligence API with AI Chat is running!",
        "version": "1.0.0",
        "database": "MongoDB",
        "ai_features": ["General Q&A Chat", "Document Analysis", "Table Processing"],
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
