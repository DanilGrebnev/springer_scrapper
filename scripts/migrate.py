#!/usr/bin/env python
"""Fully automatic database migration check & apply (aerich + Tortoise ORM).

Designed to be called from bin/ scripts before starting the app.
Handles all edge cases: first run, fresh DB, broken state, etc.
"""
import logging
import os
import shutil
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("migrate")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS_MODELS_DIR = os.path.join(PROJECT_ROOT, "migrations", "models")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "requirements", "pyproject.toml")


def _aerich(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "aerich", "-c", CONFIG_FILE, *args],
        capture_output=True,
        text=True,
    )


def _has_migration_files() -> bool:
    if not os.path.isdir(MIGRATIONS_MODELS_DIR):
        return False
    return any(
        f.endswith(".py") and f != "__init__.py"
        for f in os.listdir(MIGRATIONS_MODELS_DIR)
    )


def _init_db() -> int:
    """First-time setup: create initial migration and tables."""
    # aerich refuses init-db if the directory already exists — clean it
    if os.path.isdir(MIGRATIONS_MODELS_DIR):
        shutil.rmtree(MIGRATIONS_MODELS_DIR)

    logger.info("Creating initial migration and database schema…")
    result = _aerich("init-db", "--safe")
    out = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        logger.error("aerich init-db failed:\n%s", out)
        return 1

    logger.info("Database schema initialized successfully")
    return 0


def _upgrade() -> int:
    """Apply pending migrations."""
    logger.info("Checking for pending migrations…")
    result = _aerich("upgrade")
    out = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        # Fresh DB cloned with committed migrations — aerich table missing.
        # App's generate_schemas=True will create all tables on startup,
        # so we just warn and let the app handle it this one time.
        if "no such table" in out.lower() or "does not exist" in out.lower():
            logger.warning(
                "aerich tracking table not found — tables will be "
                "created on first app startup, migrations will apply next run"
            )
            return 0
        logger.error("aerich upgrade failed:\n%s", out)
        return 1

    if out and "no upgrade" not in out.lower():
        logger.info("Applied migrations:\n%s", out)
    else:
        logger.info("Database schema is up to date")
    return 0


def main() -> int:
    os.chdir(PROJECT_ROOT)

    from dotenv import load_dotenv
    load_dotenv()

    if _has_migration_files():
        return _upgrade()
    return _init_db()


if __name__ == "__main__":
    sys.exit(main())
