# Deployment Guide

This guide explains how the Elevaite platform CI/CD pipelines work and how to deploy to different environments.

## Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   develop   │────▶│   staging   │────▶│ production  │
│   branch    │     │    (auto)   │     │  (manual)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
  PR Checks (CI)
```

## Pipelines

### 1. CI Pipeline (`ci.yml`)

**Triggers:** Every PR and push to `develop` or `main`

**What it does:**
- Detects what files changed
- Runs linting (ESLint, Ruff)
- Runs type checking (TypeScript)
- Builds Docker images (on push only)

**Jobs:**
| Job | Runs When | Purpose |
|-----|-----------|---------|
| `changes` | Always | Detects what changed |
| `frontend` | Frontend files changed | Lint, type-check, build |
| `python` | Python files changed | Lint, format check |
| `build-*` | Push to develop + files changed | Build Docker images |

### 2. Deploy to Staging (`deploy-staging.yml`)

**Triggers:**
- Automatically on push to `develop`
- Manually via workflow dispatch

**What it does:**
1. Builds Docker images
2. Pushes to AWS ECR with `staging-*` tags
3. Deploys to staging environment

**Manual Trigger:**
```
GitHub → Actions → Deploy to Staging → Run workflow
  → Select service (all, auth-api, workflow-engine, ingestion)
  → Run
```

### 3. Deploy to Production (`deploy-prod.yml`)

**Triggers:** Manual only (never auto-deploys)

**Safety Features:**
- Requires typing "DEPLOY" to confirm
- Warns if deploying from non-main branch
- Can deploy specific services or all

**Manual Trigger:**
```
GitHub → Actions → Deploy to Production → Run workflow
  → Select service
  → Type "DEPLOY" to confirm
  → Run
```

## Required Secrets

Configure these in GitHub Repository Settings → Secrets:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key for ECR/deployment |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `ECR_REGISTRY` | ECR registry URL (e.g., `123456789.dkr.ecr.us-west-2.amazonaws.com`) |

## Required Variables

Configure in GitHub Repository Settings → Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-west-2` |

## Image Tagging Strategy

| Environment | Tag Pattern | Example |
|-------------|-------------|---------|
| CI Build | `<image>:<sha>` | `elevaite-auth-api:abc123` |
| Staging | `staging-<sha>`, `staging-latest` | `elevaite-auth-api:staging-abc123` |
| Production | `prod-<sha>`, `prod-latest` | `elevaite-auth-api:prod-abc123` |

## Adding Deployment Steps

The deploy workflows have placeholder deployment steps. Add your infrastructure-specific steps:

### AWS ECS Example

```yaml
- name: Deploy to ECS
  uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    task-definition: task-definition.json
    service: elevaite-staging
    cluster: elevaite-cluster
    wait-for-service-stability: true
```

### Kubernetes Example

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl set image deployment/auth-api \
      auth-api=${{ env.ECR_REGISTRY }}/elevaite-auth-api:staging-${{ github.sha }}
```

### Custom Script Example

```yaml
- name: Deploy via SSH
  run: |
    ssh deploy@your-server "cd /app && docker-compose pull && docker-compose up -d"
```

## Branch Protection

Recommended branch protection rules for `develop`:

1. **Require pull request reviews**
2. **Require status checks to pass:**
   - `ci-status`
3. **Require branches to be up to date**
4. **Do not allow bypassing**

## Monitoring Deployments

After deployment:

1. **Check GitHub Actions** - View deployment logs
2. **Check ECR** - Verify images were pushed
3. **Check your infrastructure** - Verify services are running

## Rollback

To rollback to a previous version:

### Option 1: Redeploy Previous Commit

```bash
# Find the previous commit SHA
git log --oneline

# Trigger deployment with that SHA
# (Create a tag or branch from that commit and deploy)
```

### Option 2: Use Previous Image

```bash
# Images are tagged with SHA, so you can:
docker pull $ECR_REGISTRY/elevaite-auth-api:staging-<previous-sha>

# Then update your deployment to use that image
```

## Troubleshooting

### CI Failing

```bash
# Run checks locally
npm run lint
npm run type-check
npm run build

# For Python
uv run ruff check python_apps/ python_packages/
uv run ruff format --check python_apps/ python_packages/
```

### Docker Build Failing

```bash
# Build locally to see errors
docker build -f python_apps/auth_api/Dockerfile -t test .
```

### ECR Push Failing

- Check AWS credentials are correct
- Check ECR repository exists
- Check IAM permissions for ECR push

### Deployment Not Updating

- Check the deployment job ran successfully
- Check the correct image tag is being used
- Check your infrastructure's deployment mechanism
