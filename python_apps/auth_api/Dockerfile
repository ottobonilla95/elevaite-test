FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
build-essential \
gcc \
libpq-dev \
python3-dev \
libffi-dev \
&& rm -rf /var/lib/apt/lists/*

# Upgrade pip and install uv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv

WORKDIR /elevaite
COPY ./python_packages/db-core ./python_packages/db-core
COPY ./python_packages/fastapi-logger ./python_packages/fastapi-logger
COPY ./python_apps/auth_api ./python_apps/auth_api
COPY ./pyproject.toml ./

RUN uv venv --python 3.11.11

ENV VIRTUAL_ENV=/elevaite/.venv \
    PATH="/elevaite/.venv/bin:$PATH"

RUN uv sync --all-packages

WORKDIR /elevaite/python_apps/auth_api/

# Expose port
EXPOSE 8004

# Run Uvicorn with reasonable performance and security settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--proxy-headers", "--timeout-keep-alive", "5", "--workers", "4", "--limit-concurrency", "100"]