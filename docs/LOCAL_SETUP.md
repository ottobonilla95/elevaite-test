# Local Development Setup

> Get the Elevaite platform running on your machine in 5 minutes.

For branching, testing, CI/CD, and code style guidelines, see the **[Developer Guide](./DEVELOPER_GUIDE.md)**.

---

## Prerequisites

- **Docker Desktop** - [Install Docker](https://docs.docker.com/get-docker/)
- **Node.js 18+** - [Install Node.js](https://nodejs.org/)

## Quick Start

```bash
# 1. Clone and install
git clone git@github.com:iopexses/elevaite.git
cd elevaite
npm install

# 2. Create environment file
cp .env.example .env
# Edit .env with your API keys (see below)

# 3. Start everything
npm run dev
```

You'll see status feedback as services start:

```
📦 Starting infrastructure (PostgreSQL, Redis, Qdrant)...
  ✅ PostgreSQL ready
  ✅ Redis ready
  ✅ Qdrant ready

🔧 Starting backend services...
  ✅ auth-api ready (port 8004)
  ✅ workflow-engine ready (port 8006)
  ✅ ingestion ready (port 8001)

🎉 ELEVAITE IS RUNNING!
```

## Services & URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Auth App | http://localhost:3005 | Login/signup UI |
| Elevaite App | http://localhost:3001 | Main application |
| Auth API Docs | http://localhost:8004/docs | API documentation |
| Workflow Engine Docs | http://localhost:8006/docs | API documentation |
| Qdrant Dashboard | http://localhost:6333/dashboard | Vector DB UI |

## Environment Variables

Create a `.env` file with at minimum:

```bash
# Required for LLM features
OPENAI_API_KEY=sk-proj-your-key-here

# Required for Google OAuth login
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
```

For the full list of environment variables, see [Developer Guide > Environment Configuration](./DEVELOPER_GUIDE.md#environment-configuration).

## Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start everything |
| `npm run dev:down` | Stop everything |
| `npm run dev:death` | Nuclear reset (wipes all data) |
| `npm run dev:logs` | View container logs |

For the full command reference, see [Developer Guide > Quick Reference](./DEVELOPER_GUIDE.md#quick-reference).

---

## Troubleshooting

### Services won't start

```bash
# Check what's running
docker ps

# View logs for a specific service
docker-compose -f docker-compose.dev.yaml logs auth-api
docker-compose -f docker-compose.dev.yaml logs workflow-engine
docker-compose -f docker-compose.dev.yaml logs ingestion
```

### Port already in use

```bash
# Find what's using a port
lsof -i :5433   # PostgreSQL
lsof -i :16379  # Redis
lsof -i :8004   # Auth API

# Kill the process or use dev:death to clean up
npm run dev:death
npm run dev
```

### Database issues

```bash
# Connect to PostgreSQL
docker exec -it elevaite-postgres psql -U elevaite -d auth

# List databases
docker exec elevaite-postgres psql -U elevaite -c "\l"
```

### Fresh start

When all else fails:

```bash
npm run dev:death
npm run dev
```

---

## Running Services Individually

For debugging, you can run backend services outside Docker:

```bash
# Start infrastructure only
npm run dev:infra

# Run a service locally (in separate terminal)
cd python_apps/auth_api
uv run uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

---

## Next Steps

- **[Developer Guide](./DEVELOPER_GUIDE.md)** - Branching, testing, CI/CD, code style
- **[Infrastructure Proposal](./INFRASTRUCTURE_PROPOSAL.md)** - Cloud architecture
