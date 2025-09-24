# Workflow Engine PoC - Dockerfile (two-stage build with uv)

FROM python:3.11-bullseye AS builder

# System deps
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv (https://github.com/astral-sh/uv)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Workspace layout
WORKDIR /elevaite

# Copy workspace config and local packages referenced by [tool.uv.sources]
COPY pyproject.toml ./
COPY python_packages/db-core ./python_packages/db-core
COPY python_packages/elevaite_ingestion ./python_packages/elevaite_ingestion
COPY python_packages/fastapi-logger ./python_packages/fastapi-logger
COPY python_packages/llm-gateway ./python_packages/llm-gateway
COPY python_packages/workflow-core-sdk ./python_packages/workflow-core-sdk


# Copy the workflow-engine-poc project
COPY python_apps/workflow-engine-poc ./python_apps/workflow-engine-poc

# Install deps (creates .venv and uv.lock)
WORKDIR /elevaite/python_apps/workflow-engine-poc
RUN uv sync


FROM python:3.11-slim-bullseye AS runtime

# Install uv in runtime stage
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin/:$PATH"

# Copy entire workspace from builder (includes .venv and uv.lock)
COPY --from=builder /elevaite /elevaite

# Working dir and port
WORKDIR /elevaite/python_apps/workflow-engine-poc
EXPOSE 8006
ENV PORT=8006

# Create uploads dir used by file APIs (non-persistent)
RUN mkdir -p /elevaite/python_apps/workflow-engine-poc/uploads

# Default command
CMD ["uv", "run", "uvicorn", "workflow_engine_poc.main:app", "--host", "0.0.0.0", "--port", "8006"]

