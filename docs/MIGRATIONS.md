# Database Migrations Guide

This document explains how database migrations work in the ElevAIte platform.

> **📘 New to migrations?** Read the [Migration Workflow Guide](./MIGRATION_WORKFLOW.md) for the complete developer workflow from local development to production deployment.

## TL;DR

```bash
# Just start dev - migrations run automatically if needed
npm run dev

# Make schema changes
cd python_apps/auth_api
uv run alembic revision --autogenerate -m "add_user_avatar"

# Commit and push - deployments handle the rest automatically
git add migrations/versions/*.py
git commit -m "feat: add user avatars"
```

## Overview

All three Python services use Alembic for database migrations:
- **auth-api**: Multi-tenant (schema-per-tenant pattern)
- **workflow-engine-poc**: Multi-tenant (schema-per-tenant pattern)
- **ingestion-service**: Single schema

**Migrations are idempotent**: They only apply if needed. Running migrations multiple times is safe and fast (~1 second if already up-to-date).

## Local Development

### Quick Start (Recommended)

Just run the dev command - migrations happen automatically:

```bash
npm run dev
```

This will:
1. Start infrastructure (PostgreSQL, RabbitMQ, Qdrant, MinIO)
2. **Automatically run all migrations** ✨
3. Start backend services
4. Start frontend apps

### Manual Migration Control

If you need more control:

```bash
# Start infrastructure only
npm run dev:infra

# Run migrations manually
npm run migrate              # All services
npm run migrate:auth         # Auth API only
npm run migrate:workflow     # Workflow Engine only
npm run migrate:ingestion    # Ingestion only

# Check migration status
npm run migrate:status

# Start services (without automatic migrations)
npm run dev:skip-migrations
```

### Skip Migrations

If migrations are already up-to-date and you want faster startup:

```bash
npm run dev:skip-migrations
# or
SKIP_MIGRATIONS=true npm run dev
```

## Creating New Migrations

### Auth API

```bash
cd python_apps/auth_api
uv run alembic revision --autogenerate -m "description"
```

### Workflow Engine

```bash
cd python_apps/workflow-engine-poc
uv run alembic revision --autogenerate -m "description"
```

### Ingestion Service

```bash
cd python_apps/ingestion-service
uv run alembic revision --autogenerate -m "description"
```

## Multi-Tenant Migrations

Auth API and Workflow Engine use schema-per-tenant pattern:

- **Schemas**: `auth_default`, `auth_toshiba`, `auth_iopex`, etc.
- **Workflow**: `workflow_default`, `workflow_toshiba`, `workflow_iopex`, etc.

### Running for Specific Tenant

```bash
# Auth API
cd python_apps/auth_api
ALEMBIC_SCHEMA=auth_default uv run alembic upgrade head

# Workflow Engine
cd python_apps/workflow-engine-poc
ALEMBIC_SCHEMA=workflow_default uv run alembic upgrade head
```

### Adding New Tenants

1. Add tenant to migration scripts:
   - Local: Edit `scripts/migrate.sh` (TENANTS env var)
   - Production: Edit `helm/elevaite/values.yaml` (migrations.tenants list)

2. Run migrations:
```bash
TENANTS="default toshiba iopex newtenant" npm run migrate
```

## Production Deployment

### Kubernetes (Automatic)

Migrations run automatically via Helm pre-upgrade hook:

```bash
helm upgrade --install elevaite ./helm/elevaite \
  --namespace production \
  --values helm/elevaite/values-production.yaml
```

The `migrations-job.yaml` runs before pods start:
- ✅ Blocks deployment if migrations fail
- ✅ Runs in parallel for all services
- ✅ Handles all tenant schemas
- ✅ Retries up to 3 times

### Manual Production Migration (if needed)

```bash
# Check migration Job status
kubectl get jobs -n production

# View migration logs
kubectl logs job/elevaite-migrations -n production

# Run migrations manually
kubectl run migrations-manual --rm -it --restart=Never \
  --image=<your-registry>/auth-api:latest \
  --namespace production \
  --env="DATABASE_URI=<db-url>" \
  -- bash -c 'cd /elevaite/python_apps/auth_api && ALEMBIC_SCHEMA=auth_default uv run alembic upgrade head'
```

## Migration Best Practices

### Do's ✅
- Always test migrations locally first
- Add both `upgrade()` and `downgrade()` functions
- Use `--autogenerate` but review the generated code
- Commit migration files to version control
- Run migrations before deploying code that depends on them

### Don'ts ❌
- Never skip migrations in production
- Don't modify existing migration files (create new ones instead)
- Don't drop columns in the same release as code changes (two-phase approach)
- Don't bypass the migration system (no manual table creation)

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -p 5433 -U elevaite -d agent_studio_sdk
# Password: elevaite
```

### Migration Conflicts

```bash
# Check current migration status
npm run migrate:status

# View migration history
cd python_apps/auth_api
uv run alembic history

# Downgrade one migration
ALEMBIC_SCHEMA=auth_default uv run alembic downgrade -1
```

### Clean Slate (Development Only)

```bash
# Nuclear reset - DESTROYS ALL DATA
npm run dev:death

# Then start fresh
npm run dev
```

### Alembic Check Fails

```bash
# Run alembic check for each service
cd python_apps/auth_api
uv run alembic check

cd ../workflow-engine-poc
uv run alembic check

cd ../ingestion-service
uv run alembic check
```

## CI/CD Integration

### CI Pipeline

The `.github/workflows/ci.yml` validates migrations:
- Runs `alembic check` to validate syntax
- Checks for duplicate revision IDs
- Blocks merge if validation fails

### Deployment Pipeline

The `.github/workflows/deploy-staging.yml`:
- Builds Docker images with migration files
- Helm hook runs migrations before deployment
- Deployment fails if migrations fail

## Architecture

### Local Development Flow

```
npm run dev
    ↓
Start Infrastructure (PostgreSQL, etc.)
    ↓
Run Migrations (scripts/migrate.sh)
    ├─ auth-api (all tenants)
    ├─ workflow-engine (all tenants)
    └─ ingestion-service
    ↓
Start Backend Services (expect tables exist)
    ↓
Start Frontend Apps
```

### Production Flow

```
Helm Upgrade
    ↓
Pre-upgrade Hook (migrations-job.yaml)
    ├─ Wait for PostgreSQL
    ├─ Run auth-api migrations (all tenants)
    ├─ Run workflow-engine migrations (all tenants)
    └─ Run ingestion-service migrations
    ↓
Deploy Pods (if migrations succeeded)
```

## File Locations

```
elevaite/
├── scripts/
│   ├── migrate.sh           # Unified migration runner
│   ├── migrate-status.sh    # Check migration status
│   └── dev.sh               # Auto-runs migrations
├── python_apps/
│   ├── auth_api/
│   │   ├── alembic.ini
│   │   └── migrations/
│   │       ├── env.py       # Multi-tenant support
│   │       └── versions/    # Migration files
│   ├── workflow-engine-poc/
│   │   ├── alembic.ini
│   │   └── alembic/
│   │       ├── env.py       # Multi-tenant support
│   │       └── versions/    # Migration files
│   └── ingestion-service/
│       ├── alembic.ini
│       └── alembic/
│           ├── env.py       # Single schema
│           └── versions/    # Migration files
└── helm/elevaite/
    ├── templates/
    │   └── migrations-job.yaml  # K8s pre-upgrade hook
    └── values.yaml              # Tenant configuration
```

## Environment Variables

### Local Development

```bash
# .env file
DATABASE_URI=postgresql://elevaite:elevaite@localhost:5433/agent_studio_sdk
DATABASE_URL=postgresql://elevaite:elevaite@localhost:5433/ingestion_db

# Override for testing
ALEMBIC_SCHEMA=auth_default  # Run migrations for specific schema
TENANTS="default toshiba"     # Override tenant list
```

### Production (Kubernetes Secrets)

```yaml
# elevaite-secrets
DATABASE_URI: postgresql://user:pass@db-host:5432/dbname
db_host: db-host.example.com
db_port: "5432"
db_user: elevaite
db_password: <secret>
```

## FAQ

**Q: Do I need to run migrations every time I start dev?**
A: No, but it's safe to. Alembic is idempotent - running migrations when already up-to-date does nothing.

**Q: What if I just cloned the repo?**
A: Just run `npm run dev`. Migrations happen automatically.

**Q: Can I use `npm run dev` even if migrations already ran?**
A: Yes! The script checks if migrations are needed and runs them only if necessary. It's smart.

**Q: How do I add a new tenant?**
A: Update `helm/elevaite/values.yaml` (migrations.tenants list), then run migrations.

**Q: What if migrations fail in production?**
A: Deployment is blocked. Fix the migration, push new commit, re-deploy. Old version keeps running.

**Q: Can I rollback a migration?**
A: Yes, use `alembic downgrade -1` but this should be rare. Better to create a new migration that reverts changes.

**Q: Where are migration files stored?**
A: In version control (git). Each service has its own `versions/` directory.

## Support

For migration issues:
1. Check this document
2. Run `npm run migrate:status` to see current state
3. Check logs: `npm run dev:logs`
4. Ask in #engineering Slack channel
