FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY ingestion_service ./ingestion_service
COPY alembic ./alembic
COPY alembic.ini ./
COPY dbos-config.yaml ./

# Expose port
EXPOSE 8000

# Run migrations and start service
CMD ["sh", "-c", "alembic upgrade head && uvicorn ingestion_service.main:app --host 0.0.0.0 --port 8000"]

