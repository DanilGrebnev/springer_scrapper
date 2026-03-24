FROM python:3.14-slim

WORKDIR /app

COPY requirements/pyproject.toml requirements/pyproject.toml

RUN pip install --no-cache-dir uv \
    && cd requirements && uv sync --no-dev \
    && cd ..

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["docker/entrypoint.sh"]
