from fastapi import FastAPI
from functools import lru_cache
from contextlib import asynccontextmanager
from app.core.database import create_db_and_tables
from .core.config import settings
from app.api.main import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await create_db_and_tables()
#     yield

app = FastAPI(
    docs_url=None,
    title=settings.APP_NAME
);

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
        title="My API Docs",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_ui_parameters={"persistAuthorization": True},
    )

app.include_router(api_router, prefix=settings.API_PATH)