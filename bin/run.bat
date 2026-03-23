@echo off
cd /d "%~dp0.."

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Syncing dependencies...
pip install --quiet requirements\

if not exist .env (
    copy .env.example .env
    echo .env created from .env.example
)

python main.py
pause
