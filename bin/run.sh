#!/bin/bash
cd "$(dirname "$0")/.."

VENV_DIR=".venv"
REQ_DIR="requirements"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Syncing dependencies..."
pip install --quiet uv 2>/dev/null
cd "$REQ_DIR" && uv sync && cd ..

if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created from .env.example"
fi

python main.py
