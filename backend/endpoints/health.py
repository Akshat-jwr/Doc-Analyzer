from fastapi import APIRouter
from db.database import check_database_health, get_database

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Health check endpoint"""
    health = await check_database_health()
    return health

@router.get("/db-info")
async def get_db_info():
    """Get database information"""
    try:
        db = await get_database()
        collections = await db.list_collection_names()
        return {
            "database_name": db.name,
            "collections": collections,
            "collection_count": len(collections)
        }
    except Exception as e:
        return {"error": str(e)}
