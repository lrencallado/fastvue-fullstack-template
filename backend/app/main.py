import logging
from fastapi import FastAPI
from functools import lru_cache
from contextlib import asynccontextmanager
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware

from app.core.database import (
    create_db_and_tables, 
    check_database_health, 
    wait_for_database,
    close_db_connections
)
from app.core.config import settings
from app.api.main import api_router
from app.middleware.error_handlers import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan with comprehensive database handling
    """
    # === STARTUP ===
    logger.info(f"🚀 Starting {settings.APP_NAME}...")
    
    try:
        # Check database health first
        logger.info("🔍 Checking database health...")
        health = await check_database_health()
        
        if health["status"] != "healthy":
            logger.error("❌ Database health check failed!")
            logger.error(f"   Error: {health['message']}")
            
            if health.get("suggestions"):
                logger.error("   💡 Suggestions:")
                for suggestion in health["suggestions"]:
                    logger.error(f"      - {suggestion}")
            
            # In development, we can be more forgiving
            if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "development":
                logger.warning("⚠️  Continuing startup in development mode...")
                logger.warning("⚠️  Some features may not work properly!")
            else:
                raise RuntimeError("Database not available - cannot start application")
        else:
            logger.info("✅ Database health check passed")
            
            # Check migration status
            migration_info = health.get("migrations", {})
            if migration_info.get("status") == "not_initialized":
                logger.warning("⚠️  No migrations detected")
                logger.warning(f"   💡 {migration_info.get('suggestion', 'Run migrations')}")
            elif migration_info.get("status") == "ok":
                logger.info(f"✅ Migrations OK (version: {migration_info.get('current_version', 'unknown')})")
        
        # Create tables in development (if using SQLModel.metadata.create_all approach)
        # Comment this out if you're using Alembic exclusively
        if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "development":
            logger.info("🔨 Creating/updating database tables for development...")
            await create_db_and_tables()
        
        logger.info("✅ Application startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # === SHUTDOWN ===
    logger.info("🛑 Shutting down application...")
    await close_db_connections()
    logger.info("✅ Shutdown completed")


# Create FastAPI app with lifespan
app = FastAPI(
    docs_url=None,
    title=settings.APP_NAME,
    lifespan=lifespan  # Enable the lifespan handler
)

# Setup exception handlers
setup_exception_handlers(app)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} Docs",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_ui_parameters={"persistAuthorization": True},
    )

# Include API routes
app.include_router(api_router, prefix=settings.API_PATH)