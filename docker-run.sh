#!/bin/bash

if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created from .env.example"
fi

docker compose -f docker/docker-compose.yml up --build -d
