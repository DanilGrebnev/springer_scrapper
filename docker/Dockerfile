FROM python:3.14-slim

WORKDIR /app

COPY requirements/pyproject.toml requirements/pyproject.toml

RUN pip install --no-cache-dir uv \
    && cd requirements && uv sync --no-dev \
    && cd ..

COPY . .

RUN sed -i 's/\r$//' /app/docker/entrypoint.sh \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/docker/entrypoint.sh"]
