import os

DATABASE_URL: str = os.getenv("DATABASE_URL") or "sqlite://db.sqlite3"

TORTOISE_CONFIG: dict = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["src.db.models", "src.admin.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
