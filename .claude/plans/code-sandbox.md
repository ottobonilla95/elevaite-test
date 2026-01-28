# Code Execution Sandbox Service - Implementation Plan

## Overview

Create a secure Code Execution Service using Nsjail for sandboxed execution of user-written and AI-generated Python code. The service will be internal-only (port 8007) and called by workers when executing "code_execution" workflow steps.

## Architecture

```
Worker (processes workflow step)
    │
    ▼
Code Execution Service (8007)
    │
    ├─► Pre-Execution Validation (AST + blocklist)
    │
    └─► Nsjail Sandbox (namespaces, seccomp, cgroups)
            │
            └─► Python execution (stdout, stderr, exit_code)
```

## Implementation Phases

### Phase 1: Core Service with Nsjail

**1.1 Create service directory structure**

```
python_apps/code-execution-service/
├── code_execution_service/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Pydantic settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── execute.py          # POST /execute
│   │   └── health.py           # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── executor.py         # Main orchestrator
│   │   ├── validator.py        # AST + blocklist validation
│   │   └── sandbox.py          # Nsjail execution
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py         # ExecuteRequest
│       └── responses.py        # ExecuteResponse
├── nsjail/
│   ├── nsjail.cfg              # Nsjail configuration
│   └── python_sandbox/
│       └── requirements.txt    # Allowed libraries (pandas, numpy)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_validator.py
│   │   └── test_executor.py
│   ├── integration/
│   │   └── test_execute_endpoint.py
│   └── security/
│       └── test_sandbox_escapes.py
├── pyproject.toml
├── Dockerfile
└── .env.example
```

**1.2 API Schema**

```python
# Request
{
    "language": "python",           # Only Python in Phase 1
    "code": "print('Hello')",       # Code to execute
    "timeout_seconds": 30,          # 1-60
    "memory_mb": 256,               # 64-512
    "input_data": {"key": "value"}  # Available as `input_data` variable
}

# Response
{
    "success": true,
    "stdout": "Hello\n",
    "stderr": "",
    "exit_code": 0,
    "execution_time_ms": 45,
    "error": null,
    "validation_errors": null
}
```

**1.3 Pre-Execution Validator**

Block dangerous imports/functions via AST parsing:
- **Blocked imports**: `os`, `subprocess`, `socket`, `requests`, `sys`, `ctypes`, `multiprocessing`, `threading`, `signal`
- **Blocked functions**: `eval`, `exec`, `compile`, `open`, `__import__`, `getattr`, `setattr`, `delattr`, `globals`, `locals`
- **Blocked patterns**: `__class__`, `__globals__`, `__subclasses__`, `__mro__`, `__code__`, `__dict__`

**1.4 Nsjail Sandbox Configuration**

Create `nsjail/nsjail.cfg` with:
```protobuf
name: "elevaite-code-sandbox"
mode: ONCE
hostname: "sandbox"
cwd: "/tmp"

# Time and resource limits
time_limit: 35
rlimit_as: 268435456    # 256MB virtual memory
rlimit_cpu: 30          # CPU seconds
rlimit_fsize: 1048576   # 1MB max file size
rlimit_nofile: 16       # Max open files
rlimit_nproc: 8         # Max processes

# Linux namespaces for isolation
clone_newnet: true      # Network isolation (no network access)
clone_newuser: true     # User namespace
clone_newns: true       # Mount namespace
clone_newpid: true      # PID namespace
clone_newipc: true      # IPC namespace
clone_newuts: true      # UTS namespace
clone_newcgroup: true   # Cgroup namespace

# Mount configuration - read-only except /tmp
mount {
    src: "/opt/sandbox"       # Pre-built Python + libs
    dst: "/opt/sandbox"
    is_bind: true
    rw: false
}
mount {
    dst: "/tmp"
    fstype: "tmpfs"
    options: "size=48m"
    rw: true
}
mount {
    dst: "/proc"
    fstype: "proc"
    rw: false
}
```

**1.5 Multi-stage Dockerfile**

```dockerfile
# Stage 1: Build Nsjail
FROM debian:bookworm-slim AS nsjail-builder
RUN apt-get update && apt-get install -y \
    git make g++ pkg-config \
    libprotobuf-dev protobuf-compiler \
    libnl-3-dev libnl-route-3-dev libcap-dev
WORKDIR /build
RUN git clone https://github.com/google/nsjail.git && \
    cd nsjail && make && mv nsjail /nsjail

# Stage 2: Build Python sandbox environment
FROM python:3.11.11-slim-bullseye AS sandbox-builder
WORKDIR /opt/sandbox
RUN python -m venv /opt/sandbox && \
    /opt/sandbox/bin/pip install --no-cache-dir \
        pandas==2.1.4 numpy==1.26.3 python-dateutil==2.8.2

# Stage 3: Runtime
FROM python:3.11.11-slim-bullseye AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libprotobuf32 libnl-3-200 libnl-route-3-200 libcap2 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=nsjail-builder /nsjail /usr/bin/nsjail
COPY --from=sandbox-builder /opt/sandbox /opt/sandbox

RUN pip install --no-cache-dir uv
WORKDIR /elevaite
COPY pyproject.toml uv.lock ./
COPY python_apps/code-execution-service ./python_apps/code-execution-service
WORKDIR /elevaite/python_apps/code-execution-service
RUN uv sync --frozen --no-dev

COPY python_apps/code-execution-service/nsjail /app/nsjail
RUN mkdir -p /tmp/sandbox && chmod 755 /tmp/sandbox

EXPOSE 8007
CMD ["uvicorn", "code_execution_service.main:app", "--host", "0.0.0.0", "--port", "8007"]
```

**1.6 Files to create**

| File | Description |
|------|-------------|
| `python_apps/code-execution-service/pyproject.toml` | Dependencies |
| `python_apps/code-execution-service/code_execution_service/main.py` | FastAPI app |
| `python_apps/code-execution-service/code_execution_service/core/config.py` | Settings |
| `python_apps/code-execution-service/code_execution_service/routers/execute.py` | `/execute` endpoint |
| `python_apps/code-execution-service/code_execution_service/routers/health.py` | `/health` endpoint |
| `python_apps/code-execution-service/code_execution_service/services/validator.py` | AST + blocklist |
| `python_apps/code-execution-service/code_execution_service/services/sandbox.py` | Nsjail executor |
| `python_apps/code-execution-service/code_execution_service/services/executor.py` | Orchestrator |
| `python_apps/code-execution-service/code_execution_service/schemas/requests.py` | ExecuteRequest |
| `python_apps/code-execution-service/code_execution_service/schemas/responses.py` | ExecuteResponse |
| `python_apps/code-execution-service/nsjail/nsjail.cfg` | Nsjail config |
| `python_apps/code-execution-service/nsjail/python_sandbox/requirements.txt` | Allowed libs |
| `python_apps/code-execution-service/Dockerfile` | Multi-stage build |
| `python_apps/code-execution-service/tests/conftest.py` | Pytest fixtures |
| `python_apps/code-execution-service/tests/unit/test_validator.py` | Validator tests |
| `python_apps/code-execution-service/tests/security/test_sandbox_escapes.py` | Security tests |

**1.7 Update docker-compose.dev.yaml**

Add after `ingestion` service (~line 227):
```yaml
code-execution:
  build:
    context: .
    dockerfile: python_apps/code-execution-service/Dockerfile
  container_name: elevaite-code-execution
  ports:
    - "8007:8007"
  environment:
    SERVICE_PORT: "8007"
    LOG_LEVEL: DEBUG
    DEFAULT_TIMEOUT_SECONDS: "30"
    MAX_MEMORY_MB: "256"
    NSJAIL_CONFIG_PATH: /app/nsjail/nsjail.cfg
  # Nsjail requires these capabilities
  cap_add:
    - SYS_ADMIN
    - SYS_PTRACE
    - NET_ADMIN
  security_opt:
    - seccomp:unconfined
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8007/health"]
    interval: 5s
    timeout: 5s
    retries: 10
    start_period: 15s
```

**1.8 Update worker environment**

Add to `worker` and `workflow-engine` services in docker-compose.dev.yaml:
```yaml
CODE_EXECUTION_SERVICE_URL: http://code-execution:8007
```

---

### Phase 2: Worker Integration

**2.1 Create workflow step type**

Add `python_packages/workflow-core-sdk/workflow_core_sdk/steps/code_execution_step.py`:
```python
async def code_execution_step(step_config, input_data, execution_context):
    """Execute code via Code Execution Service"""
    cfg = step_config.get("config", {})
    service_url = os.getenv("CODE_EXECUTION_SERVICE_URL", "http://localhost:8007")

    async with httpx.AsyncClient(timeout=cfg.get("timeout", 30) + 5) as client:
        response = await client.post(
            f"{service_url}/execute",
            json={
                "language": "python",
                "code": cfg.get("code", ""),
                "timeout_seconds": cfg.get("timeout", 30),
                "memory_mb": cfg.get("memory_mb", 256),
                "input_data": input_data,
            },
        )
        return response.json()
```

**2.2 Register step in registry**

Update `workflow_core_sdk/execution/registry_impl.py` to include the new step type.

---

### Phase 3: Production Deployment

**3.1 Create Helm template**

Create `helm/elevaite/templates/code-execution-deployment.yaml` following the `ingestion-deployment.yaml` pattern.

**3.2 Update Helm values.yaml**

The `codeExecution` section already exists (lines 171-202). Update `securityContext` for Nsjail:
```yaml
securityContext:
  privileged: false
  capabilities:
    add:
      - SYS_ADMIN
      - SYS_PTRACE
      - NET_ADMIN
```

---

## Critical Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` (root) | Modify | Add workspace member: `"python_apps/code-execution-service"` |
| `docker-compose.dev.yaml` | Modify | Add code-execution service + env vars for worker |
| `helm/elevaite/values.yaml` | Modify | Update `codeExecution.securityContext` |

## Critical Files to Create

| File | Description |
|------|-------------|
| `python_apps/code-execution-service/` | New service directory (all files listed above) |
| `helm/elevaite/templates/code-execution-deployment.yaml` | K8s deployment template |

## Dependencies (pyproject.toml)

```toml
[project]
name = "code-execution-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["code_execution_service"]
```

## Verification Steps

### Phase 1 Verification

1. **Build Docker image**:
   ```bash
   docker-compose -f docker-compose.dev.yaml build code-execution
   ```

2. **Start service**:
   ```bash
   npm run dev  # or docker-compose -f docker-compose.dev.yaml up code-execution
   ```

3. **Health check**:
   ```bash
   curl http://localhost:8007/health
   # Expected: {"status": "healthy"}
   ```

4. **Simple execution**:
   ```bash
   curl -X POST http://localhost:8007/execute \
     -H "Content-Type: application/json" \
     -d '{"code": "print(1 + 1)", "timeout_seconds": 5}'
   # Expected: {"success": true, "stdout": "2\n", "exit_code": 0, ...}
   ```

5. **Input data works**:
   ```bash
   curl -X POST http://localhost:8007/execute \
     -H "Content-Type: application/json" \
     -d '{"code": "import json\nprint(sum(input_data[\"nums\"]))", "input_data": {"nums": [1,2,3]}}'
   # Expected: {"success": true, "stdout": "6\n", ...}
   ```

6. **Dangerous code blocked (validation)**:
   ```bash
   curl -X POST http://localhost:8007/execute \
     -d '{"code": "import os; os.system(\"ls\")"}'
   # Expected: {"success": false, "validation_errors": ["Blocked import: os"]}
   ```

7. **Network blocked (Nsjail)**:
   ```bash
   curl -X POST http://localhost:8007/execute \
     -d '{"code": "import urllib.request; urllib.request.urlopen(\"http://google.com\")"}'
   # Expected: failure (network namespace blocks it)
   ```

8. **Timeout enforced**:
   ```bash
   curl -X POST http://localhost:8007/execute \
     -d '{"code": "while True: pass", "timeout_seconds": 2}'
   # Expected: {"success": false, "exit_code": -1, ...} (killed by timeout)
   ```

9. **Unit tests pass**:
   ```bash
   cd python_apps/code-execution-service
   uv run pytest tests/unit -v
   ```

10. **Security tests pass**:
    ```bash
    uv run pytest tests/security -v
    ```

### Phase 2 Verification

1. Create a test workflow with `code_execution` step type
2. Execute workflow via workflow-engine API
3. Verify code execution results appear in execution output

## Allowed Libraries (Sandbox)

Pre-installed in `/opt/sandbox`:
- `pandas`, `numpy` - Data processing
- `python-dateutil` - Date utilities

Available from Python stdlib:
- `json`, `math`, `datetime`, `collections`, `itertools`, `functools`
- `re`, `decimal`, `fractions`, `statistics`, `random`
- `string`, `textwrap`, `unicodedata`

## Blocked (Defense in Depth)

**Layer 1 - Validator (AST + Regex)**:
- Imports: `os`, `subprocess`, `socket`, `requests`, `urllib`, `http`, `sys`, `ctypes`, `multiprocessing`
- Functions: `eval`, `exec`, `compile`, `open`, `__import__`, `getattr`, `setattr`
- Patterns: `__class__`, `__globals__`, `__subclasses__`, `__mro__`

**Layer 2 - Nsjail**:
- Network: `clone_newnet` blocks all network access
- Filesystem: Read-only except `/tmp` (48MB tmpfs)
- Processes: `rlimit_nproc: 8` limits fork bombs
- Memory: `rlimit_as: 256MB` virtual memory limit
- CPU: `time_limit: 35s` hard timeout
- Syscalls: seccomp-bpf filtering (optional, can add later)

## Security Layers Summary

| Layer | Technology | What it blocks |
|-------|------------|----------------|
| L1 | AST parsing | Dangerous imports, functions |
| L1 | Regex patterns | Dunder methods, attribute access |
| L2 | Nsjail network namespace | All network access |
| L2 | Nsjail mount namespace | Filesystem outside /tmp |
| L2 | Nsjail cgroups | Memory/CPU exhaustion |
| L2 | Nsjail PID namespace | Process tree visibility |
| L3 (optional) | seccomp-bpf | Dangerous syscalls |
