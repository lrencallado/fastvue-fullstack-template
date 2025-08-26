import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from asyncpg.exceptions import InvalidCatalogNameError

from app.exceptions import DatabaseConnectionError, BaseAPIException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for your FastAPI + SQLModel + Alembic stack"""
    
    @app.exception_handler(DatabaseConnectionError)
    async def database_connection_handler(request: Request, exc: DatabaseConnectionError):
        logger.error(f"Database connection error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": exc.message,
                "error_code": "DATABASE_CONNECTION_ERROR",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(request: Request, exc: BaseAPIException):
        logger.warning(f"API exception: {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])
            errors.append({
                "field": field if field else None,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(InvalidCatalogNameError)
    async def catalog_error_handler(request: Request, exc: InvalidCatalogNameError):
        """Handle the specific error you encountered"""
        logger.error(f"Database catalog error: {exc}")
        
        db_name = str(request.app.extra.get('settings', {}).get('SQLALCHEMY_DATABASE_URI', '')).split('/')[-1]
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": f"Database '{db_name}' does not exist",
                "error_code": "DATABASE_NOT_FOUND",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "details": {
                    "database_name": db_name,
                    "suggestions": [
                        f"Create database: createdb -h localhost -U postgres {db_name}",
                        "Run: python scripts/setup_dev_db.py",
                        "Check your database configuration"
                    ]
                },
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"Database integrity error: {exc}")
        
        message = "Data integrity constraint violated"
        if "unique constraint" in str(exc.orig).lower():
            message = "Resource already exists"
        elif "foreign key constraint" in str(exc.orig).lower():
            message = "Referenced resource not found"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": message,
                "error_code": "INTEGRITY_ERROR",
                "status_code": status.HTTP_409_CONFLICT,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )