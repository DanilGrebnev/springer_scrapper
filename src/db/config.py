import os

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required and must point to a PostgreSQL database")

if not DATABASE_URL.startswith(("postgres://", "postgresql://")):
    raise RuntimeError("DATABASE_URL must use postgres:// or postgresql:// scheme")

TORTOISE_CONFIG: dict = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["src.db.models", "src.admin.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
