from fastapi import FastAPI
from src.config import config
from src import routes


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_title,
        version=config.app_version,
    )
    app.include_router(routes.health.router)
    return app


app = create_app()
