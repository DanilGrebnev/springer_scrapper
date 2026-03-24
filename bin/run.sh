#!/bin/bash
cd "$(dirname "$0")/.."

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    pip install --quiet uv 2>/dev/null
fi

echo "Syncing dependencies..."
cd requirements && uv sync && cd ..

if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created from .env.example"
fi

echo "Checking database migrations..."
uv run --project requirements python scripts/migrate.py || { echo "Migration check failed!"; exit 1; }

uv run --project requirements python main.py
