from fastapi import FastAPI
from functools import lru_cache
from contextlib import asynccontextmanager
from app.core.database import create_db_and_tables
from .core.config import settings
from app.api.main import api_router

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await create_db_and_tables()
#     yield

app = FastAPI(
    title=settings.APP_NAME
);

@app.get("/")
async def root():
    return {"message": "Hello World!"}

app.include_router(api_router, prefix=settings.API_PATH)