import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import config
from src import routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_title,
        version=config.app_version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes.health.router)
    app.include_router(routes.article_search.router)
    app.include_router(routes.ai_test.router)
    return app


app = create_app()
