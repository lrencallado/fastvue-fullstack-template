from fastapi import APIRouter
from app.api.routes import private, login
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(login.router)

if (settings.APP_ENV == "local" or settings.APP_ENV == "staging"):
    api_router.include_router(private.router)