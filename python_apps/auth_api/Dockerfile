FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install uv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY ./pyproject.toml .

# Use uv to install dependencies quickly
RUN uv pip install --system -e .

# Copy application code
COPY ./app ./app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set secure environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTAPI_ENV=production \
    PORT=8000

# Set permissions
RUN chmod -R 550 /app

# Expose port
EXPOSE 8000

# Run Uvicorn with reasonable performance and security settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--timeout-keep-alive", "5", "--workers", "4", "--limit-concurrency", "100"]