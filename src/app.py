import src._compat  # noqa: F401 — aioredis patch, must precede fastapi_admin

import logging
import os
from contextlib import asynccontextmanager

import fakeredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_admin.app import app as admin_app
from fastapi_admin.exceptions import (
    forbidden_error_exception,
    not_found_error_exception,
    server_error_exception,
    unauthorized_error_exception,
)
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from tortoise.contrib.fastapi import register_tortoise

from src import routes
from src.admin.provider import login_provider
from src.agent.ai_executor import shutdown_ai_executor
from src.config import config
from src.db import TORTOISE_CONFIG, check_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

_ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "changeme-replace-in-production")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Инициализируем fastapi-admin
    redis = fakeredis.FakeAsyncRedis(decode_responses=True)
    await admin_app.configure(
        logo_url="https://preview.tabler.io/static/logo-white.svg",
        favicon_url="https://raw.githubusercontent.com/fastapi-admin/fastapi-admin/dev/images/favicon.png",
        providers=[login_provider],
        redis=redis,
    )
    # Проверяем доступность БД (Tortoise уже инициализирован через register_tortoise)
    await check_db()
    yield
    shutdown_ai_executor(wait=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_title,
        version=config.app_version,
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    admin_app.add_exception_handler(HTTP_500_INTERNAL_SERVER_ERROR, server_error_exception)
    admin_app.add_exception_handler(HTTP_404_NOT_FOUND, not_found_error_exception)
    admin_app.add_exception_handler(HTTP_403_FORBIDDEN, forbidden_error_exception)
    admin_app.add_exception_handler(HTTP_401_UNAUTHORIZED, unauthorized_error_exception)

    app.mount("/admin", admin_app)

    app.include_router(routes.health.router)
    app.include_router(routes.auth.router)
    app.include_router(routes.article_search.router)
    app.include_router(routes.ai_test.router)
    app.include_router(routes.pdf.router)

    register_tortoise(
        app,
        config=TORTOISE_CONFIG,
        generate_schemas=True,
    )

    return app


app = create_app()
