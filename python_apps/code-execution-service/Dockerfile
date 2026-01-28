# Code Execution Service - Multi-stage Dockerfile
# Stage 1: Build Nsjail
# Stage 2: Build Python sandbox environment
# Stage 3: Runtime

# ============================================================
# Stage 1: Build Nsjail from source
# ============================================================
FROM debian:bookworm-slim AS nsjail-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    g++ \
    pkg-config \
    flex \
    bison \
    libprotobuf-dev \
    protobuf-compiler \
    libnl-3-dev \
    libnl-route-3-dev \
    libcap-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Clone and build nsjail
RUN git clone --depth 1 https://github.com/google/nsjail.git && \
    cd nsjail && \
    make && \
    mv nsjail /nsjail

# ============================================================
# Stage 2: Build Python sandbox environment with allowed libs
# ============================================================
FROM python:3.11-slim-bookworm AS sandbox-builder

WORKDIR /opt/sandbox

# Create virtual environment and install allowed libraries
RUN python -m venv /opt/sandbox && \
    /opt/sandbox/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/sandbox/bin/pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    python-dateutil==2.8.2

# ============================================================
# Stage 3: Runtime
# ============================================================
FROM python:3.11-slim-bookworm AS runtime

# Prevent Python from writing .pyc files and ensure logs are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies for nsjail
RUN apt-get update && apt-get install -y --no-install-recommends \
    libprotobuf32 \
    libnl-3-200 \
    libnl-route-3-200 \
    libcap2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy nsjail binary from builder
COPY --from=nsjail-builder /nsjail /usr/bin/nsjail
RUN chmod +x /usr/bin/nsjail

# Copy sandbox Python environment from builder
COPY --from=sandbox-builder /opt/sandbox /opt/sandbox

# Install uv for Python package management
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Set up workspace root inside the container
WORKDIR /elevaite

# Copy workspace configuration and lockfile
COPY pyproject.toml uv.lock ./

# Copy the code-execution-service project
COPY python_apps/code-execution-service ./python_apps/code-execution-service

# Install Python dependencies for the service
WORKDIR /elevaite/python_apps/code-execution-service
RUN uv sync --no-dev

# Copy nsjail configuration
COPY python_apps/code-execution-service/nsjail /app/nsjail

# Create sandbox temp directory
RUN mkdir -p /tmp/sandbox && chmod 755 /tmp/sandbox

# Ensure the virtual environment is on PATH
ENV PATH="/elevaite/.venv/bin:/elevaite/python_apps/code-execution-service/.venv/bin:${PATH}"

# Expose the service port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Start the service
CMD ["uvicorn", "code_execution_service.main:app", "--host", "0.0.0.0", "--port", "8007"]

