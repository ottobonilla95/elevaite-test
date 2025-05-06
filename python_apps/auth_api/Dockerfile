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
COPY ./python_apps/auth_api ./python_apps/auth_api
COPY ./pyproject.toml ./

WORKDIR /elevaite/python_apps/auth_api/
RUN uv venv --python 3.11.11

RUN uv sync

# # Create non-root user
# RUN adduser --disabled-password --gecos "" appuser
# RUN chown -R appuser:appuser /app
# USER appuser

# # Set secure environment variables
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     FASTAPI_ENV=production \
#     PORT=8004

# # Set permissions
# RUN chmod -R 550 /app

# Expose port
EXPOSE 8004

# Run Uvicorn with reasonable performance and security settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--proxy-headers", "--timeout-keep-alive", "5", "--workers", "4", "--limit-concurrency", "100"]