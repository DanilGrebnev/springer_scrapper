@echo off
cd /d "%~dp0.."

uv --version >nul 2>&1 || (
    echo Installing uv...
    pip install --quiet uv 2>nul
)

echo Syncing dependencies...
cd requirements && uv sync && cd ..

if not exist .env (
    copy .env.example .env
    echo .env created from .env.example
)

echo Checking database migrations...
uv run --project requirements python scripts\migrate.py
if errorlevel 1 (
    echo Migration check failed!
    pause
    exit /b 1
)

uv run --project requirements python main.py
pause
