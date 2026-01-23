# Elevaite Developer Guide

> Comprehensive guide for developers working on the Elevaite platform. Covers branching strategy, testing, CI/CD, configuration, and seed data.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Branching Strategy](#branching-strategy)
3. [Pull Request Guidelines](#pull-request-guidelines)
4. [Testing](#testing)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Environment Configuration](#environment-configuration)
7. [Seed Data & Test Accounts](#seed-data--test-accounts)
8. [Code Style & Conventions](#code-style--conventions)

---

## Getting Started

### Prerequisites

- **Node.js** >= 18
- **Python** >= 3.11
- **Docker Desktop** (for local development)
- **Git**

### Quick Start

```bash
# Clone the repository
git clone git@github.com:iopexses/elevaite.git
cd elevaite

# Install dependencies
npm install

# Create your .env file (see Environment Configuration section)
cp .env.example .env

# Start local development
npm run dev
```

For detailed local setup instructions, see [LOCAL_SETUP.md](./LOCAL_SETUP.md).

---

## Branching Strategy

We follow a **trunk-based development** model with short-lived feature branches.

### Branch Types

| Branch | Purpose | Naming Convention | Merges To |
|--------|---------|-------------------|-----------|
| `main` | Production-ready code | - | - |
| `develop` | Integration branch for staging | - | `main` |
| `feature/*` | New features | `feature/TICKET-123-short-description` | `develop` |
| `fix/*` | Bug fixes | `fix/TICKET-123-short-description` | `develop` |
| `hotfix/*` | Urgent production fixes | `hotfix/TICKET-123-short-description` | `main` + `develop` |
| `chore/*` | Maintenance, docs, config | `chore/short-description` | `develop` |
| `refactor/*` | Code refactoring | `refactor/short-description` | `develop` |

### Branch Naming Rules

- Use **lowercase** with **hyphens** (no underscores or spaces)
- Include **ticket number** when applicable (e.g., `feature/ELV-123-add-user-auth`)
- Keep descriptions **short but meaningful** (3-5 words max)

### Workflow

```
main ←────────────────────────────────────────── Production releases
  ↑
develop ←──────────────────────────────────────── Staging/Integration
  ↑
feature/ELV-123-my-feature ←───────────────────── Your work here
```

1. **Create branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/ELV-123-add-workflow-triggers
   ```

2. **Work on your feature** with regular commits

3. **Push and create PR** to `develop`:
   ```bash
   git push -u origin feature/ELV-123-add-workflow-triggers
   ```

4. **After review and CI passes**, merge to `develop`

5. **Staging deployment** happens automatically on merge to `develop`

6. **Production deployment** is manual, triggered from `main`

### Protected Branches

| Branch | Requirements |
|--------|-------------|
| `main` | PR required, 1 approval, CI must pass, no direct pushes |
| `develop` | PR required, CI must pass |

---

## Pull Request Guidelines

### PR Title Convention (Conventional Commits)

PR titles **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <short description>
```

**Types:**

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add email trigger for workflows` |
| `fix` | Bug fix | `fix: resolve memory leak in scheduler` |
| `docs` | Documentation only | `docs: update API documentation` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `refactor` | Code refactoring | `refactor: simplify auth middleware` |
| `test` | Adding/updating tests | `test: add unit tests for workflow engine` |
| `style` | Code style (formatting) | `style: fix linting errors` |
| `perf` | Performance improvements | `perf: optimize database queries` |
| `ci` | CI/CD changes | `ci: add staging deployment workflow` |
| `build` | Build system changes | `build: update Docker configuration` |

**Rules:**
- Maximum 80 characters
- Use present tense ("add" not "added")
- No period at the end
- Lowercase (except for acronyms)

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] Tested in local environment

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #123
```

### PR Checklist

Before requesting review:

- [ ] Code follows project style guidelines
- [ ] Self-reviewed my code
- [ ] Added/updated tests as needed
- [ ] All tests pass locally (`npm run test`)
- [ ] Linting passes (`npm run lint`)
- [ ] Documentation updated if needed
- [ ] PR title follows conventional commits

---

## Testing

> **Status:** ✅ Python tests run in CI with coverage (40% minimum). ✅ Frontend tests (Vitest) are configured.

### Test Structure

```
elevaite/
├── tests/                          # Global integration tests
│   └── unit/
├── python_apps/
│   ├── auth_api/
│   │   └── tests/                  # Auth API tests
│   ├── workflow-engine-poc/
│   │   └── tests/                  # Workflow engine tests
│   └── ingestion-service/
│       └── tests/                  # Ingestion service tests
├── python_packages/
│   ├── workflow-core-sdk/
│   │   └── tests/                  # SDK tests
│   └── rbac-sdk/
│       └── tests/                  # RBAC tests
└── apps/
    ├── auth/
    │   └── __tests__/              # Frontend auth tests
    └── elevaite/
        └── __tests__/              # Frontend elevaite tests
```

### Running Tests

#### Python Tests

```bash
# Run all Python tests
pytest

# Run with coverage
pytest --cov=python_apps --cov=python_packages --cov-report=html

# Run specific test file
pytest python_apps/auth_api/tests/test_auth.py

# Run tests matching a pattern
pytest -k "test_workflow"

# Run with verbose output
pytest -v

# Run only fast unit tests (exclude integration)
pytest -m "not integration"
```

#### Frontend Tests (Vitest)

```bash
# Run all frontend tests
npm run test:frontend

# Run tests for specific app
cd apps/auth && npm test
cd apps/elevaite && npm test

# Run with coverage
cd apps/auth && npm run test:coverage

# Run in watch mode (interactive)
cd apps/auth && npm run test:watch
```

### Test Types

| Type | Location | Purpose | Markers |
|------|----------|---------|---------|
| **Unit Tests** | `*/tests/unit/` | Test individual functions/classes | `@pytest.mark.unit` |
| **Integration Tests** | `*/tests/integration/` | Test API endpoints, DB operations | `@pytest.mark.integration` |
| **E2E Tests** | `*/tests/e2e/` | Full user flow testing | `@pytest.mark.e2e` |

### Writing Tests

#### Python Test Example

```python
# python_apps/auth_api/tests/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
@pytest.mark.unit
async def test_login_success():
    """Test successful user login."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
    
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
@pytest.mark.unit
async def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
    
    assert response.status_code == 401
```

#### Frontend Test Example

```typescript
// apps/auth/__tests__/login.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from '../app/login/page';

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows error on invalid credentials', async () => {
    render(<LoginPage />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrong' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
  });
});
```

### Code Coverage

> **Current Status:** Coverage reporting is available locally. CI integration with coverage thresholds is planned.

#### Coverage Targets (Goals)

| Component | Target Coverage |
|-----------|-----------------|
| Python APIs | 70% |
| Python SDKs | 80% |
| Frontend Apps | 60% |
| Critical Paths (auth, payments) | 90% |

#### Viewing Coverage Reports

```bash
# Python - generates HTML report in htmlcov/
npm run test:python:cov
open htmlcov/index.html

# Or manually:
pytest --cov=python_apps --cov=python_packages --cov-report=html
```

#### Coverage in CI (Planned)

Coverage thresholds will be enforced in CI once the test suite is stable. Currently, tests run but coverage is not blocking.

---

## CI/CD Pipeline

### Pipeline Overview

```
Push/PR to develop
        │
        ▼
┌───────────────────┐
│   CI Pipeline     │
│  (GitHub Actions) │
├───────────────────┤
│ ✓ Lint            │
│ ✓ Type Check      │
│ ✓ Unit Tests      │
│ ✓ Build Docker    │
│ ✓ PR Title Check  │
└───────────────────┘
        │
        ▼ (on merge to develop)
┌───────────────────┐
│ Staging Deploy    │
│ (Automatic)       │
└───────────────────┘
        │
        ▼ (manual trigger)
┌───────────────────┐
│ Production Deploy │
│ (Manual)          │
└───────────────────┘
```

### CI Checks (`.github/workflows/ci.yml`)

Every PR triggers:

| Check | Description | Required | Status |
|-------|-------------|----------|--------|
| `pr-title` | Conventional commit validation | ✅ Yes | ✅ Active |
| `lint` | ESLint + Ruff | ✅ Yes | ✅ Active |
| `type-check` | TypeScript | ✅ Yes | ✅ Active |
| `test:python` | Python unit tests | ⚠️ Non-blocking | ✅ Active |
| `build` | Docker image build | ✅ Yes | ✅ Active |
| `test:frontend` | Frontend tests | ❌ Not yet | 🔜 Planned |
| `coverage` | Coverage thresholds | ❌ Not yet | 🔜 Planned |

### Deployment Environments

| Environment | Branch | Trigger | URL |
|-------------|--------|---------|-----|
| **Staging** | `develop` | Automatic on merge | `https://staging.elevaite.io` |
| **Production** | `main` | Manual approval | `https://app.elevaite.io` |

### Kubernetes Deployment

Deployments use **Helm charts** located in `helm/elevaite/`.

```bash
# Deploy to staging (automatic on merge to develop)
helm upgrade --install elevaite ./helm/elevaite \
  -f ./helm/elevaite/values-staging.yaml \
  --namespace elevaite-staging

# Deploy to production (manual, requires typing "DEPLOY" to confirm)
# Triggered via GitHub Actions workflow_dispatch
```

**Helm values files:**
- `values.yaml` - Default values
- `values-staging.yaml` - Staging overrides
- `values-production.yaml` - Production overrides

For infrastructure details, see [INFRASTRUCTURE.md](./INFRASTRUCTURE.md).

### Running CI Locally

Before pushing, run the same checks CI will run:

```bash
# Lint
npm run lint

# Type check
npm run type-check

# Tests
pytest
npm run test

# Build Docker images
docker-compose -f docker-compose.dev.yaml build
```

---

## Environment Configuration

### Environment Files

| File | Purpose | Committed? |
|------|---------|------------|
| `.env.example` | Template with all required variables | ✅ Yes |
| `.env` | Local development secrets | ❌ No |
| `.env.staging` | Staging environment (CI/CD only) | ❌ No |
| `.env.production` | Production environment (CI/CD only) | ❌ No |

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# ==================== AI / LLM ====================
OPENAI_API_KEY=sk-proj-your-key-here
GEMINI_API_KEY=your-gemini-key-here

# ==================== OAuth / Auth ====================
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here

# FusionAuth (legacy - being phased out)
FUSIONAUTH_CLIENT_ID=your-fusionauth-client-id
FUSIONAUTH_CLIENT_SECRET=your-fusionauth-secret
FUSIONAUTH_API_KEY=your-fusionauth-api-key

# ==================== Databases ====================
# These are set automatically in docker-compose for local dev
# Only needed if running services outside Docker

# Auth API
AUTH_DB_URL=postgresql+asyncpg://elevaite:elevaite@localhost:5433/auth

# Workflow Engine
WORKFLOW_DB_URL=postgresql://elevaite:elevaite@localhost:5433/workflow_engine

# Ingestion Service
INGESTION_DB_URL=postgresql://elevaite:elevaite@localhost:5433/elevaite_ingestion

# ==================== Cache ====================
REDIS_HOST=localhost
REDIS_PORT=16379

# ==================== Vector Database ====================
QDRANT_HOST=localhost
QDRANT_PORT=6333

# ==================== AWS (Production) ====================
# Not needed for local dev - dummy values are used
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-west-1
S3_BUCKET_NAME=elevaite-uploads

# ==================== Service URLs ====================
INGESTION_SERVICE_URL=http://localhost:8001
WORKFLOW_ENGINE_URL=http://localhost:8006
AUTH_API_URL=http://localhost:8004
```

### Getting API Keys

| Service | How to Get |
|---------|------------|
| OpenAI | https://platform.openai.com/api-keys |
| Google OAuth | https://console.cloud.google.com/apis/credentials |
| Gemini | https://makersuite.google.com/app/apikey |
| AWS | Contact DevOps team |

### Environment-Specific Settings

| Setting | Local | Staging | Production |
|---------|-------|---------|------------|
| `DEBUG` | `1` | `0` | `0` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| Database | Docker (localhost:5433) | RDS | RDS |
| Redis | Docker (localhost:16379) | ElastiCache | ElastiCache |
| S3 | Not used (local storage) | S3 Bucket | S3 Bucket |

---

## Seed Data & Test Accounts

### Local Development Data

When you run `npm run dev`, the following is automatically created:

#### Databases

| Database | Purpose |
|----------|---------|
| `auth` | User authentication, sessions, MFA |
| `workflow_engine` | Workflows, executions, steps |
| `elevaite_ingestion` | Document ingestion, embeddings |

#### Tenant Schemas

The platform uses schema-based multitenancy. These schemas are auto-created:

| Schema | Purpose |
|--------|---------|
| `auth_default` | Default tenant auth data |
| `auth_toshiba` | Toshiba tenant auth data |
| `auth_iopex` | Iopex tenant auth data |
| `wf_default` | Default tenant workflows |
| `wf_iopex` | Iopex tenant workflows |
| `public` | Shared/scheduler data |

### Test Accounts

For local development, create test accounts via the Auth API:

```bash
# Create a test user
curl -X POST http://localhost:8004/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@elevaite.local",
    "password": "DevPassword123!",
    "first_name": "Dev",
    "last_name": "User"
  }'
```

#### Pre-configured Test Accounts (Staging Only)

| Email | Password | Role | Tenant |
|-------|----------|------|--------|
| `admin@elevaite.io` | `AdminTest123!` | Admin | default |
| `user@elevaite.io` | `UserTest123!` | User | default |
| `viewer@elevaite.io` | `ViewerTest123!` | Viewer | default |

> ⚠️ **Never use test credentials in production!**

### Seeding Sample Data

#### Seed Workflows

```bash
# Seed sample workflows (run from project root)
python scripts/seed_workflows.py

# Or via API
curl -X POST http://localhost:8006/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: default" \
  -d @workflows/sample_workflow.json
```

#### Seed Documents (for RAG testing)

```bash
# Upload a test document
curl -X POST http://localhost:8001/api/v1/documents/upload \
  -H "X-Tenant-ID: default" \
  -F "file=@test_documents/ai_research_paper.txt"
```

### Database Reset

To completely reset local data:

```bash
# Nuclear option - wipes everything
npm run dev:death

# Then restart
npm run dev
```

To reset just the database (keep Docker images):

```bash
npm run dev:clean  # Removes volumes
npm run dev
```

---

## Code Style & Conventions

### Python

- **Formatter:** Black (line-length: 120)
- **Linter:** Ruff
- **Type Hints:** Required for all public functions

```python
# Good
def process_workflow(workflow_id: str, tenant_id: str) -> WorkflowResult:
    """Process a workflow and return the result."""
    ...

# Bad
def process_workflow(workflow_id, tenant_id):
    ...
```

### TypeScript/JavaScript

- **Formatter:** Prettier
- **Linter:** ESLint
- **Style:** Functional components, hooks

```typescript
// Good
interface UserProps {
  name: string;
  email: string;
}

export function UserCard({ name, email }: UserProps) {
  return (
    <div>
      <h2>{name}</h2>
      <p>{email}</p>
    </div>
  );
}

// Bad
export function UserCard(props: any) {
  return <div>{props.name}</div>;
}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Good
git commit -m "feat: add email notification for workflow completion"
git commit -m "fix: resolve race condition in scheduler"
git commit -m "docs: update API documentation for v2 endpoints"

# Bad
git commit -m "fixed stuff"
git commit -m "WIP"
git commit -m "updates"
```

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| Python modules | `snake_case.py` | `workflow_engine.py` |
| Python classes | `PascalCase` | `WorkflowEngine` |
| TypeScript files | `kebab-case.tsx` | `user-profile.tsx` |
| React components | `PascalCase.tsx` | `UserProfile.tsx` |
| Test files | `test_*.py` / `*.test.ts` | `test_auth.py`, `auth.test.ts` |

---

## Quick Reference

### Common Commands

```bash
# Development
npm run dev              # Start everything with status feedback
npm run dev:down         # Stop everything
npm run dev:logs         # View all logs
npm run dev:death        # Nuclear reset

# Testing
npm run test:python      # Run Python tests
npm run test:python:cov  # Run with coverage report
pytest -k "test_name"    # Run specific test

# Code Quality
npm run lint             # Lint all code
npm run type-check       # Type check all code
npm run format           # Format all code

# Docker
docker-compose -f docker-compose.dev.yaml build --no-cache <service>
docker-compose -f docker-compose.dev.yaml logs -f <service>
```

### Service Ports (Local)

| Service | Port | URL |
|---------|------|-----|
| Auth App | 3005 | http://localhost:3005 |
| Elevaite App | 3001 | http://localhost:3001 |
| Auth API | 8004 | http://localhost:8004/docs |
| Workflow Engine | 8006 | http://localhost:8006/docs |
| Ingestion Service | 8001 | http://localhost:8001/docs |
| PostgreSQL | 5433 | `localhost:5433` |
| Redis | 16379 | `localhost:16379` |
| Qdrant | 6333 | http://localhost:6333/dashboard |

---

## Getting Help

- **Documentation:** Check the `docs/` folder
- **Slack:** #elevaite-dev channel
- **Issues:** Create a GitHub issue with the `question` label

---

*Last updated: January 2026*
