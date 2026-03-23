@echo off
cd /d "%~dp0.."

if not exist .env (
    copy .env.example .env
    echo .env created from .env.example
)

docker compose -f docker/docker-compose.yml up --build -d
pause
