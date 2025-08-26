from fastapi import APIRouter
from app.api.routes import private, login, users, health
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(health.router)

if (settings.ENVIRONMENT == "local" or settings.ENVIRONMENT == "development"):
    api_router.include_router(private.router)