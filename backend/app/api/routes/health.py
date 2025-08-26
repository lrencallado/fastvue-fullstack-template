from fastapi import APIRouter
from app.core.database import (
    check_database_health, 
)
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Comprehensive health check endpoint"""
    db_health = await check_database_health()
    
    return {
        "api_status": "healthy",
        "app_name": settings.APP_NAME,
        "database": db_health,
        "environment": getattr(settings, 'ENVIRONMENT', 'unknown')
    }


@router.get("/database")
async def database_health():
    """Detailed database health endpoint for monitoring"""
    return await check_database_health()
