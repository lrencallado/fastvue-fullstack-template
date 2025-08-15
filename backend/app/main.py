from fastapi import FastAPI
from . import config
from functools import lru_cache
from contextlib import asynccontextmanager
from app.database import create_db_and_tables
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(
    title=settings.app_name
);

@app.get("/")
async def root():
    return {"message": "Hello World!"}