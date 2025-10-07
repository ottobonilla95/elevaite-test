FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  curl \
  build-essential \
  gcc \
  libpq-dev \
  python3-dev \
  libffi-dev \
  && rm -rf /var/lib/apt/lists/*

# Install uv (modern way)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /elevaite

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy project files do buidl
COPY . .
RUN uv sync --frozen

# Caller will exec into pod so leave it running until explicitly killed
CMD ["sleep", "infinity"]