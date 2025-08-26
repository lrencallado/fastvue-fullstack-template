import logging
from typing import Dict, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from asyncpg.exceptions import InvalidCatalogNameError, ConnectionDoesNotExistError
from sqlmodel import SQLModel
from sqlalchemy import text

from app.core.config import settings
from app.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

# Create async engine with error handling configuration
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.DB_DEBUG,
    pool_size=10,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    connect_args={
        "command_timeout": 30,  # 30 seconds timeout for commands
        "statement_cache_size": 0,  # Disable statement caching to avoid memory issues
    }
)

async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with comprehensive error handling
    """
    session = None
    try:
        session = async_session()
        yield session
        await session.commit()
    except (OperationalError, InvalidCatalogNameError) as e:
        logger.error(f"Database connection error: {e}")
        if session:
            await session.rollback()
        raise DatabaseConnectionError(f"Unable to connect to database: {str(e)}")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()


async def check_database_health() -> Dict[str, Any]:
    """
    Check database connection and return detailed health status
    """
    try:
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as health_check"))
            result.fetchone()
        
        # Test if migrations are up to date
        migration_status = await check_migration_status()
        
        return {
            "status": "healthy",
            "database_exists": True,
            "connection": "ok",
            "migrations": migration_status,
            "message": "Database is healthy and accessible"
        }
        
    except InvalidCatalogNameError:
        db_name = str(settings.SQLALCHEMY_DATABASE_URI).split("/")[-1]
        return {
            "status": "error",
            "database_exists": False,
            "connection": "failed",
            "error_type": "database_not_found",
            "message": f"Database '{db_name}' does not exist",
            "suggestions": [
                f"Create database: createdb -h {settings.DB_HOST} -U {settings.DB_USERNAME} {db_name}",
                f"Or using psql: CREATE DATABASE {db_name};",
                "Run: python scripts/setup_dev_db.py (for development)"
            ]
        }
        
    except (ConnectionDoesNotExistError, OperationalError) as e:
        return {
            "status": "error",
            "database_exists": None,
            "connection": "failed",
            "error_type": "connection_failed",
            "message": f"Cannot connect to database server: {str(e)}",
            "suggestions": [
                "Check if PostgreSQL server is running",
                f"Verify connection: {settings.DB_HOST}:{settings.DB_PORT}",
                "Check credentials and network connectivity"
            ]
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "database_exists": None,
            "connection": "unknown",
            "error_type": "unknown",
            "message": f"Health check failed: {str(e)}"
        }


async def check_migration_status() -> Dict[str, Any]:
    """
    Check if Alembic migrations are up to date
    """
    try:
        async with engine.begin() as conn:
            # Check if alembic_version table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """))
            table_exists = (result.fetchone())[0]
            
            if not table_exists:
                return {
                    "status": "not_initialized",
                    "message": "No migrations have been run yet",
                    "suggestion": "Run: alembic upgrade head"
                }
            
            # Get current migration version
            result = await conn.execute(text(
                "SELECT version_num FROM alembic_version;"
            ))
            current_version = (result.fetchone())[0] if result.rowcount > 0 else None
            
            return {
                "status": "ok",
                "current_version": current_version,
                "message": "Migrations are initialized"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not check migration status: {str(e)}"
        }


async def create_db_and_tables():
    """
    Create database tables - Use only in development!
    For production, use Alembic migrations instead.
    """
    if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "production":
        logger.warning("Skipping table creation in production - use Alembic migrations")
        return
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise DatabaseConnectionError(f"Failed to create database tables: {str(e)}")


async def wait_for_database(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """
    Wait for database to become available (useful for Docker environments)
    """
    import asyncio
    
    for attempt in range(max_retries):
        logger.info(f"Database connection attempt {attempt + 1}/{max_retries}")
        
        health = await check_database_health()
        
        if health["status"] == "healthy":
            logger.info("Database connection established ✅")
            return True
        
        if health.get("error_type") == "database_not_found":
            logger.error("❌ Database does not exist - manual intervention required")
            if health.get("suggestions"):
                for suggestion in health["suggestions"]:
                    logger.error(f"   💡 {suggestion}")
            return False
        
        logger.warning(f"⏳ Database not ready: {health['message']}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_interval)
    
    logger.error("❌ Database connection failed after all retries")
    return False


async def close_db_connections():
    """Close all database connections gracefully"""
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")