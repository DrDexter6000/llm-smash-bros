FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs && apt-get clean
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
RUN cd frontend && npm run build
COPY backend/pyproject.toml backend/uv.lock* backend/
RUN cd backend && uv sync --no-dev
COPY backend/ backend/
EXPOSE 8000
CMD ["uv", "run", "--directory", "backend", "python", "-m", "llm_smash", "--serve", "--port", "8000"]
