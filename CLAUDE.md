# CLAUDE.md

This file provides guidance to Claude Code when working with the ElevAIte platform codebase.

## Project Overview

**ElevAIte** is an AI workflow automation platform where users build, deploy, and interact with intelligent agents.

- **What it does:** Users create workflows visually (Agent Studio), deploy them, and interact via chat
- **Core concept:** Build workflows → Execute workflows → Process results
- **Architecture:** Next.js frontends + Python/FastAPI backends + Worker pattern (RabbitMQ queues)
- **Deployment:** Kubernetes (EKS/AKS/GKE) with Terraform + Helm
- **Multi-tenancy:** Schema-per-tenant pattern in PostgreSQL

## Repository Structure

```
elevaite/
├── apps/                           # Frontend Next.js applications
│   ├── auth/                       # Authentication UI (port 3005)
│   └── elevaite/                   # Main application UI (port 3001)
├── packages/                       # Shared frontend packages
│   ├── ui/                         # Component library
│   ├── lib/                        # Shared utilities
│   └── config-*/                   # Shared configs (ESLint, TypeScript, Tailwind)
├── python_apps/                    # Backend services (FastAPI)
│   ├── auth_api/                   # Authentication API (port 8004)
│   ├── workflow-engine-poc/        # Workflow execution engine (port 8006)
│   └── ingestion-service/          # Document processing/RAG (port 8001)
├── python_packages/                # Shared Python libraries
│   ├── workflow-core-sdk/          # Workflow SDK
│   ├── rbac-sdk/                   # Authorization SDK
│   ├── elevaite_ingestion/         # Ingestion utilities
│   └── db-core/                    # Database utilities
├── terraform/                      # Infrastructure as code (multi-cloud)
│   ├── modules/                    # Reusable modules
│   ├── environments/               # Per-environment configs
│   └── bootstrap/                  # Initial setup
├── helm/                          # Kubernetes deployment
│   └── elevaite/                  # Main Helm chart
├── docs/                          # Documentation
│   ├── LOCAL_SETUP.md             # Local development setup
│   ├── DEVELOPER_GUIDE.md         # Contributing guide
│   └── INFRASTRUCTURE.md          # Infrastructure architecture
└── .github/workflows/             # CI/CD pipelines
    ├── ci.yml                     # Lint, test, type-check
    ├── deploy-staging.yml         # Deploy to staging
    └── deploy-prod.yml            # Deploy to production
```

## Active Services

**IMPORTANT:** Only these services are actively used (see `docker-compose.dev.yaml`):

### Infrastructure
- **PostgreSQL** (5433) - Primary database
- **Qdrant** (6333) - Vector database for RAG
- **RabbitMQ** (5672, 15672) - Message queues for async tasks
- **MinIO** (9000, 9001) - S3-compatible object storage

### Backend Services (Python/FastAPI)
- **auth-api** (8004) - Authentication, authorization, user/tenant management
- **workflow-engine** (8006) - Agent execution, chat handling, tool orchestration
- **ingestion** (8001) - Document processing, embeddings, vector storage

### Frontend (Next.js)
- **auth** (3005) - Login/signup UI, OAuth flows
- **elevaite** (3001) - Agent Studio, chat interface, dashboards

### Workers
- Workers consume RabbitMQ queues and execute long-running tasks
- Same codebase as workflow-engine, running in "worker mode"

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React, TypeScript, Tailwind CSS |
| **Backend** | Python 3.11.11, FastAPI, SQLModel |
| **Database** | PostgreSQL, Qdrant (vector DB) |
| **Queue** | RabbitMQ |
| **Storage** | MinIO (S3-compatible) |
| **Infrastructure** | Docker, Kubernetes, Terraform, Helm |
| **Monorepo** | Turborepo (frontend), uv (Python) |
| **Linting** | ESLint (TS), Ruff (Python) |
| **Testing** | pytest (Python), Vitest/Jest (TS) |
| **CI/CD** | GitHub Actions |

## Build/Lint/Test Commands

### Development
```bash
# Start all services (infra + backend + frontend)
npm run dev

# Start individual layers (advanced)
npm run dev:infra        # Start infrastructure only
npm run dev:backend      # Start backend services
npm run dev:frontend     # Start frontend apps

# Stop everything
npm run dev:down

# Nuclear reset (wipes all data)
npm run dev:death
```

### Build
```bash
npm run build              # Build main apps (auth + elevaite)
npm run build:all          # Build all apps
```

### Linting
```bash
# Frontend
npm run lint               # Lint main apps
npm run lint:all           # Lint all frontend code

# Python
npm run lint:python        # Lint Python apps
npm run lint:python:fix    # Auto-fix Python issues

# All
npm run lint:all           # Lint everything
```

### Type Checking
```bash
npm run type-check         # Type-check main apps
npm run type-check:all     # Type-check all frontend code
```

### Testing
```bash
# Frontend
npm run test:frontend      # Test main apps

# Python
npm run test:python        # Run all Python tests
npm run test:python:cov    # Run with coverage report

# Single test file
uv run pytest path/to/test_file.py

# Single test function
uv run pytest path/to/test_file.py::test_function_name

# Test by marker
uv run pytest -m unit      # Only unit tests
uv run pytest -m integration  # Only integration tests
```

### Formatting
```bash
npm run format             # Format TS/TSX/MD files
npm run format:python      # Format Python code
npm run format:all         # Format everything
```

## Code Style

### TypeScript/Next.js
- **Strict mode:** Use strict TypeScript with proper interfaces
- **Components:** Functional components with hooks
- **Naming:** camelCase for variables/functions, PascalCase for components
- **Imports:** Group by external/internal/relative
- **Styling:** Tailwind CSS classes, SCSS modules for complex components
- **Error handling:** Use error boundaries and try/catch
- **File structure:** Follow Next.js conventions (app router)

### Python
- **Style:** PEP8 with type hints
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Type hints:** Required for all function signatures
- **Async:** Use async/await consistently
- **Error handling:** Use proper exception handling
- **Imports:** Group by stdlib/third-party/local
- **Linting:** Ruff (replaces flake8, isort, black)
- **Package manager:** uv (fast Rust-based pip replacement)

### Python Testing
```python
# Use pytest markers
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_function():
    pass

# Markers available:
# - unit: Unit tests
# - integration: Integration tests
# - functional: Functional tests
# - redis: Tests requiring Redis
# - openai: Tests requiring OpenAI API
# - network: Tests requiring network access
```

## Key Concepts

### Workflows
- Users build workflows in Agent Studio (visual node-based editor)
- Workflows are stored in PostgreSQL
- Workflow Engine executes workflows via LLM + tools
- Workers handle long-running tasks via RabbitMQ queues

### Multi-Tenancy
- **Pattern:** Schema-per-tenant in PostgreSQL
- **Isolation:** Each tenant has their own database schema
- **Authentication:** JWT tokens with tenant context
- **Authorization:** RBAC with role/permission checks

### RAG (Retrieval-Augmented Generation)
- Documents uploaded → Ingestion Service
- Processing pipeline: PARSING → CHUNKING → EMBEDDING → VECTOR_DB
- Embeddings stored in Qdrant
- LLM queries retrieve relevant chunks for context

### Async Task Pattern
```
User Request → Workflow Engine → RabbitMQ → Worker → Result
```

## Database Migrations

### Python (Alembic)
```bash
# Create migration
cd python_apps/auth_api
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

**Migration Rules:**
- Migrations must be backwards compatible
- Add columns first, deploy code, then remove old columns later
- Never drop columns in same deploy as code changes
- Migrations run automatically in CI/CD pipeline

## Python Workspace Setup

**Package Manager:** uv (Rust-based, faster than pip)

```bash
# Install dependencies
uv sync

# Add dependency to specific app
cd python_apps/auth_api
uv add fastapi

# Add dev dependency
uv add --dev pytest

# Run commands with uv
uv run pytest
uv run ruff check .
```

**Workspace Structure:**
- Root `pyproject.toml` defines workspace members
- Each app/package has its own `pyproject.toml`
- Shared dependencies in workspace root

## Pre-commit Hooks

**Husky + lint-staged** runs on commit:
- Python: `ruff check --fix` + `ruff format`
- TypeScript: `eslint --fix` + `prettier --write`

**Files checked:**
- `python_apps/{auth_api,workflow-engine-poc,ingestion-service}/**/*.py`
- `python_packages/**/*.py`
- `*.{ts,tsx}`

## Infrastructure

### Local Development
- **Infrastructure:** Docker Compose (`docker-compose.dev.yaml`)
- **Services:** PostgreSQL, RabbitMQ, MinIO, Qdrant run in containers
- **Backends:** Build from Dockerfiles, connect to local infra
- **Frontends:** Run with `npm run dev`, connect to local backends

### Staging/Production
- **Cloud:** Kubernetes (EKS/AKS/GKE)
- **Infrastructure:** Terraform provisions managed services
- **Deployment:** Helm charts deploy applications
- **Database:** Managed PostgreSQL (RDS/Cloud SQL/Azure DB)
- **Queue:** CloudAMQP or Amazon MQ
- **Storage:** S3/Azure Blob/GCS (S3-compatible API)

### Terraform
- **Location:** `terraform/`
- **Modules:** Multi-cloud (AWS/Azure/GCP)
- **Environments:** dev, staging, production
- **Managed Services:** PostgreSQL, RabbitMQ, Kubernetes, object storage

### Helm
- **Location:** `helm/elevaite/`
- **Charts:** Deploy all services to Kubernetes
- **Values:** Per-environment overrides (staging, production)

## CI/CD Pipeline

**Active workflows:**
- `ci.yml` - Lint, test, type-check on PR
- `deploy-staging.yml` - Auto-deploy on merge to `develop`
- `deploy-prod.yml` - Manual deploy on merge to `main`

**Pipeline stages:**
1. **Lint** - ESLint, Ruff
2. **Type check** - TypeScript, Python type hints
3. **Test** - pytest (Python), Vitest (TS)
4. **Build** - Docker images
5. **Deploy** - Helm upgrade to Kubernetes

## Git Workflow

- **Main branch:** `develop` (for PRs, staging deploys)
- **Production branch:** `main` (for production deploys)
- **Commit style:** Conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- **Pre-commit:** Automatic linting/formatting via Husky

## Common Tasks

### Add a new API endpoint (Python)
1. Add route in `python_apps/<service>/app/routes/`
2. Add business logic in `app/services/`
3. Add tests in `tests/`
4. Run tests: `uv run pytest`
5. Check types/lint: `npm run lint:python`

### Add a new frontend component
1. Create component in `packages/ui/` or `apps/<app>/components/`
2. Use TypeScript with proper types
3. Style with Tailwind CSS
4. Add to component library exports if shared
5. Run type-check: `npm run type-check`

### Debug locally
```bash
# Check logs
npm run dev:logs

# Access services
# - RabbitMQ UI: http://localhost:15672 (elevaite/elevaite)
# - MinIO console: http://localhost:9001 (minioadmin/minioadmin)
# - PostgreSQL: localhost:5433 (elevaite/elevaite)

# Check database
psql -h localhost -p 5433 -U elevaite -d auth
```

### Run specific service

**Recommended:** Use docker-compose for backend services (ensures correct env vars):
```bash
# Run only a specific backend service
docker-compose -f docker-compose.dev.yaml up auth-api
docker-compose -f docker-compose.dev.yaml up workflow-engine
docker-compose -f docker-compose.dev.yaml up ingestion
```

**For frontend only:**
```bash
cd apps/elevaite
npm run dev
# OR
cd apps/auth
npm run dev
```

**Advanced - Running Python services standalone** (for debugging):
```bash
# Export env vars from root .env first
set -a; source .env; set +a

# Then run the service
cd python_apps/workflow-engine-poc
uv run uvicorn app.main:app --reload --port 8006
```

## Environment Variables

### Local Development

**Single `.env` file at repo root** - Copy from `.env.example`:
```bash
cp .env.example .env
```

**Required for local dev:**
- `OPENAI_API_KEY` - For LLM calls
- `GOOGLE_CLIENT_ID` - For OAuth
- `GOOGLE_CLIENT_SECRET` - For OAuth

**All other vars** (database, RabbitMQ, frontend URLs) have defaults in `.env.example`.

### GitHub Repository Variables (CI/CD)

For staging/production deployments, these variables are set in GitHub repo settings.

**Location:** Repo → Settings → Secrets and variables → Actions

#### GitHub Secrets (sensitive - use "Secrets" tab)

| Secret | Purpose |
|--------|---------|
| `OPENAI_API_KEY` | LLM API access |
| `GOOGLE_CLIENT_ID` | OAuth authentication |
| `GOOGLE_CLIENT_SECRET` | OAuth authentication |
| `JWT_SECRET` | Token signing |
| `NEXTAUTH_SECRET` | NextAuth session encryption |
| `STAGING_DB_USER` | Staging database username |
| `STAGING_DB_PASSWORD` | Staging database password |
| `STAGING_STORAGE_ACCESS_KEY` | S3/MinIO access (staging) |
| `STAGING_STORAGE_SECRET_KEY` | S3/MinIO secret (staging) |
| `STAGING_RABBITMQ_PASSWORD` | Message queue auth (staging) |
| `STAGING_QDRANT_API_KEY` | Vector DB auth (staging, optional) |
| `PROD_DB_USER` | Production database username |
| `PROD_DB_PASSWORD` | Production database password |
| `PROD_STORAGE_ACCESS_KEY` | S3/MinIO access (production) |
| `PROD_STORAGE_SECRET_KEY` | S3/MinIO secret (production) |
| `PROD_RABBITMQ_PASSWORD` | Message queue auth (production) |
| `PROD_QDRANT_API_KEY` | Vector DB auth (production, optional) |
| `AWS_ACCESS_KEY_ID` | AWS deployment credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS deployment credentials |

#### GitHub Variables (non-sensitive URLs - use "Variables" tab)

| Variable | Purpose | Example |
|----------|---------|---------|
| `CLOUD_PROVIDER` | Target cloud (aws/azure/gcp) | `aws` |
| `AWS_REGION` | AWS region | `us-west-1` |
| `STAGING_BACKEND_URL` | Workflow engine URL (staging) | `https://api-staging.example.com` |
| `STAGING_AUTH_API_URL` | Auth API URL (staging) | `https://auth-staging.example.com` |
| `STAGING_AUTH_URL` | Auth frontend URL (staging) | `https://login-staging.example.com` |
| `PROD_BACKEND_URL` | Workflow engine URL (production) | `https://api.example.com` |
| `PROD_AUTH_API_URL` | Auth API URL (production) | `https://auth.example.com` |
| `PROD_AUTH_URL` | Auth frontend URL (production) | `https://login.example.com` |

**Note:** If deploy workflows fail with "missing variable" errors, check this list.

## Important Files

- `docker-compose.dev.yaml` - Local development environment
- `package.json` - Frontend scripts and dependencies
- `pyproject.toml` - Python workspace config
- `pytest.ini` - Python test configuration
- `turbo.json` - Turborepo pipeline config
- `.github/workflows/ci.yml` - CI pipeline
- `docs/INFRASTRUCTURE.md` - Architecture reference

## Documentation

- **Local Setup:** `docs/LOCAL_SETUP.md`
- **Developer Guide:** `docs/DEVELOPER_GUIDE.md`
- **Infrastructure:** `docs/INFRASTRUCTURE.md`
- **README:** `README.md` (quick start)

## Notes for Claude

### When working on this codebase:

1. **Only modify active services** - See docker-compose.dev.yaml for what's actually used
2. **Follow existing patterns** - Check similar code before adding new features
3. **Use proper types** - TypeScript strict mode, Python type hints required
4. **Test your changes** - Run relevant tests before committing
5. **Check the infra docs** - Reference INFRASTRUCTURE.md for architecture questions
6. **Use the right commands** - Frontend: npm scripts, Python: uv run
7. **Multi-tenancy aware** - All queries must filter by tenant_id
8. **Async by default** - Use async/await in Python, especially for DB operations
9. **Pre-commit will run** - Linting/formatting happens automatically via Husky

### Common pitfalls to avoid:

- Don't modify legacy apps (arlo, exceltoppt, media, etc.) - they're being removed
- Don't use pip directly - always use `uv`
- Don't skip tenant filtering - security risk
- Don't bypass pre-commit hooks
- Don't add dependencies without considering monorepo impact
- Don't commit secrets or .env files
- Don't modify Terraform without understanding multi-cloud modules

### When in doubt:

- Check existing code for patterns
- Read the relevant documentation in `docs/`
- Look at test files for usage examples
- Ask for clarification if requirements are unclear
