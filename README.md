# Elevaite Platform

> AI Workflow Automation Platform - Build, deploy, and interact with intelligent agents.

## Quick Start

```bash
# Clone and install
git clone git@github.com:iopexses/elevaite.git
cd elevaite
npm install

# Create your .env file
cp .env.example .env
# Edit .env with your API keys (OpenAI, Google OAuth, etc.)

# Start everything
npm run dev
```

Once running, open:
- **Auth App:** http://localhost:3005
- **Elevaite App:** http://localhost:3001

## Documentation

| Document | When to Read |
|----------|--------------|
| 📦 **[Local Setup](docs/LOCAL_SETUP.md)** | Get running locally, troubleshoot issues |
| 👩‍💻 **[Developer Guide](docs/DEVELOPER_GUIDE.md)** | Before contributing: branching, testing, PRs |
| ☁️ **[Infrastructure](docs/INFRASTRUCTURE.md)** | Understand production architecture |

## Repository Structure

```
elevaite/
├── apps/                    # Frontend applications (Next.js)
│   ├── auth/               # Authentication UI
│   └── elevaite/           # Main application UI
├── packages/               # Shared frontend packages
│   └── ui/                 # Component library
├── python_apps/            # Backend services
│   ├── auth_api/           # Authentication API
│   ├── workflow-engine-poc/ # Workflow execution engine
│   └── ingestion-service/  # Document processing
├── python_packages/        # Shared Python libraries
│   ├── workflow-core-sdk/  # Workflow SDK
│   └── rbac-sdk/           # Authorization SDK
└── docs/                   # Documentation
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLModel |
| Database | PostgreSQL, Redis, Qdrant (Vector DB) |
| Infrastructure | Docker, AWS ECS (prod), Vercel (frontend) |

## Common Commands

```bash
npm run dev          # Start all services with status feedback
npm run dev:down     # Stop everything
npm run dev:death    # Nuclear reset (wipes all data)
npm run lint         # Run linters
npm run test:python  # Run Python tests
```

## Contributing

1. Read the [Developer Guide](docs/DEVELOPER_GUIDE.md)
2. Create a branch following our naming convention
3. Make your changes with tests
4. Submit a PR with a [conventional commit](https://www.conventionalcommits.org/) title

---
