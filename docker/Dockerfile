FROM python:3.14-slim

WORKDIR /app

COPY requirements/pyproject.toml requirements/pyproject.toml

RUN pip install --no-cache-dir uv \
    && cd requirements && uv sync --no-dev \
    && cd ..

COPY . .

EXPOSE 8000

CMD ["uv", "run", "--project", "requirements", "python", "main.py"]
