# Workflow Engine PoC - Dockerfile (two-stage build with uv)

FROM python:3.11.11-slim-bullseye AS builder

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Set up the workspace structure
WORKDIR /elevaite

# Copy workspace configuration
COPY pyproject.toml uv.lock ./

# Copy workspace package dependencies used by workflow-engine-poc
COPY python_packages/db-core ./python_packages/db-core
COPY python_packages/fastapi-logger ./python_packages/fastapi-logger
COPY python_packages/llm-gateway ./python_packages/llm-gateway
COPY python_packages/rbac-sdk ./python_packages/rbac-sdk
COPY python_packages/workflow-core-sdk ./python_packages/workflow-core-sdk

# Copy workflow-engine-poc project files
COPY python_apps/workflow-engine-poc ./python_apps/workflow-engine-poc

# Install dependencies using uv in the workflow-engine-poc directory
WORKDIR /elevaite/python_apps/workflow-engine-poc

# Increase timeout for slow networks during dependency downloads
ENV UV_HTTP_TIMEOUT=120

# Install dependencies using uv (this will create .venv automatically)
RUN uv sync --frozen --no-dev
# Copy the created venv to a stable location outside the source tree to avoid bind-mount masking
RUN mkdir -p /opt && if [ -d "/elevaite/.venv" ]; then \
    cp -a /elevaite/.venv /opt/venv; \
    else \
    cp -a /elevaite/python_apps/workflow-engine-poc/.venv /opt/venv; \
    fi
# Remove source-embedded venvs to avoid duplication when copying app sources
RUN rm -rf /elevaite/.venv /elevaite/python_apps/workflow-engine-poc/.venv || true


FROM python:3.11.11-slim-bullseye AS runtime

# Copy only the app sources needed at runtime (dependencies are in /opt/venv)
COPY --from=builder /elevaite/python_apps/workflow-engine-poc /elevaite/python_apps/workflow-engine-poc
COPY --from=builder /elevaite/python_packages/db-core /elevaite/python_packages/db-core
COPY --from=builder /elevaite/python_packages/fastapi-logger /elevaite/python_packages/fastapi-logger
COPY --from=builder /elevaite/python_packages/llm-gateway /elevaite/python_packages/llm-gateway
COPY --from=builder /elevaite/python_packages/rbac-sdk /elevaite/python_packages/rbac-sdk
COPY --from=builder /elevaite/python_packages/workflow-core-sdk /elevaite/python_packages/workflow-core-sdk
# Copy the virtual environment to runtime
COPY --from=builder /opt/venv /opt/venv


# Use the prebuilt virtual environment (relocated to /opt/venv)
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Change to the workflow-engine-poc application directory
WORKDIR /elevaite/python_apps/workflow-engine-poc

# Expose the port
EXPOSE 8006

# Set environment variable for port
ENV PORT=8006

# Create uploads dir used by file APIs (non-persistent)
RUN mkdir -p /elevaite/python_apps/workflow-engine-poc/uploads

# Run the application using the prebuilt environment (resolved via PATH)
# Verify uvicorn is installed in the relocated venv (fail build early if missing)
RUN python -c "import uvicorn, sys; print(uvicorn.__version__)"
# Start the API server
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "workflow_engine_poc.main:app", "--host", "0.0.0.0", "--port", "8006"]

