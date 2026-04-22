#!/bin/sh
set -e

echo "Checking database migrations..."
uv run --project requirements python scripts/migrate.py

echo "Starting application..."
exec uv run --project requirements python main.py
