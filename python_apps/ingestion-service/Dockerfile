FROM python:3.11.11-slim-bullseye

# Prevent Python from writing .pyc files and ensure logs are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required for building DBOS, Postgres drivers and ingestion libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    libffi-dev \
    curl \
    ca-certificates \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv as the Python package/dependency manager
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

# Set up workspace root inside the container
WORKDIR /elevaite

# Copy workspace configuration and lockfile
COPY pyproject.toml uv.lock ./

# Copy only the packages needed by the ingestion service
COPY python_packages/elevaite_ingestion ./python_packages/elevaite_ingestion

# Copy the ingestion service project (including alembic and DBOS config)
COPY python_apps/ingestion-service ./python_apps/ingestion-service

# Install Python dependencies for the ingestion service (uv will create/manage the virtualenv)
WORKDIR /elevaite/python_apps/ingestion-service
# Increase timeout for slow networks during dependency downloads
ENV UV_HTTP_TIMEOUT=120
# Use non-frozen sync so the container build does not depend on a fully-updated lockfile
RUN uv sync --no-dev

# Ensure the virtual environment is on PATH (uv may place it at workspace or project root)
ENV PATH="/elevaite/.venv/bin:/elevaite/python_apps/ingestion-service/.venv/bin:${PATH}"

# Expose the FastAPI port
EXPOSE 8000

# Start the service (migrations should be run separately via Kubernetes Job or manual script)
CMD ["uvicorn", "ingestion_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

