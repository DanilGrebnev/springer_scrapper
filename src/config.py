import os


class AppConfig:
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    app_title: str = os.getenv("APP_TITLE", "Springer Scrapper API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")


config = AppConfig()
