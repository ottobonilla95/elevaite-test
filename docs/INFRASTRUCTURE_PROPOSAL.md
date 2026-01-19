# ElevAIte Platform - Infrastructure Proposal

## Executive Summary

This document outlines the recommended cloud infrastructure for the ElevAIte AI workflow automation platform. The architecture prioritizes **simplicity, scalability, and cost-effectiveness** using proven patterns from the industry.

**Key decisions:**
- **ECS Fargate** for backend services.
- **Vercel** for frontend (automatic PR previews)
- **Queue + Workers** pattern for task execution (not pod-per-workflow)
- **Terraform** for infrastructure as code

---

## Platform Overview

ElevAIte is an AI workflow automation platform where users:
1. **Build** agents visually in Agent Studio (drag-and-drop nodes)
2. **Deploy** agents to make them available
3. **Interact** via chat interface - agents execute actions (query databases, send emails, call APIs, etc.)

---

## Platform Components

### Frontend (Next.js on Vercel)

| App | Port (local) | Purpose |
|-----|--------------|---------|
| **Auth App** | 3005 | Login/signup UI, OAuth flows |
| **ElevAIte App** | 3001 | Agent Studio, chat interface, dashboards |

### Backend (Python on ECS Fargate)

| Service | Port | Purpose |
|---------|------|---------|
| **Auth API** | 8004 | Authentication, authorization, user/tenant management |
| **Workflow Engine** | 8006 | Agent execution, chat handling, tool orchestration |

### Workers (Python on ECS Fargate)

| Component | Purpose |
|-----------|---------|
| **Workers** | Poll SQS queues, execute long-running tasks (report generation, batch processing) |

Workers are the same codebase as Workflow Engine, running in "worker mode" - polling queues instead of serving HTTP requests.

### Data Layer

| Component | Purpose |
|-----------|---------|
| **PostgreSQL (RDS)** | Primary database - users, tenants, agents, workflows, execution logs |
| **Qdrant Cloud** | Vector database - document embeddings for RAG (retrieval) |
| **S3** | File storage - uploaded files, generated reports |
| **SQS** | Message queues for async task processing |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    USERS                                        │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDFLARE (DNS)                                   │
└───────────────────┬─────────────────────────────────────────┬───────────────────┘
                    │                                         │
                    ▼                                         ▼
┌───────────────────────────────────┐     ┌───────────────────────────────────────┐
│            VERCEL                 │     │                 AWS                   │
│          (Frontend)               │     │                                       │
│                                   │     │  ┌─────────────────────────────────┐  │
│  • Auth App (3105)                │     │  │   Application Load Balancer     │  │
│  • ElevAIte App (3101)            │────▶│  └───────────────┬─────────────────┘  │
│  • PR Previews                    │     │                  │                    │
│                                   │     │  ┌───────────────▼─────────────────┐  │
└───────────────────────────────────┘     │  │      ECS FARGATE CLUSTER        │  │
                                          │  │                                 │  │
                                          │  │  ┌───────────┐ ┌─────────────┐  │  │
                                          │  │  │ Auth API  │ │  Workflow   │  │  │
                                          │  │  │  (8004)   │ │   Engine    │  │  │
                                          │  │  │           │ │   (8006)    │  │  │
                                          │  │  └───────────┘ └─────────────┘  │  │
                                          │  │                                 │  │
                                          │  │  ┌───────────────────────────┐  │  │
                                          │  │  │         WORKERS           │  │  │
                                          │  │  │  • Poll SQS for tasks     │  │  │
                                          │  │  │  • Execute long jobs      │  │  │
                                          │  │  │  • Auto-scale on demand   │  │  │
                                          │  │  └───────────────────────────┘  │  │
                                          │  └─────────────────────────────────┘  │
                                          │                  │                    │
                                          │  ┌───────────────▼─────────────────┐  │
                                          │  │          DATA LAYER             │  │
                                          │  │                                 │  │
                                          │  │  ┌─────────┐    ┌─────────┐    │  │
                                          │  │  │   RDS   │    │   S3    │    │  │
                                          │  │  │Postgres │    │ (Files) │    │  │
                                          │  │  └─────────┘    └─────────┘    │  │
                                          │  │                                 │  │
                                          │  │  ┌───────────────────────────┐  │  │
                                          │  │  │           SQS             │  │  │
                                          │  │  │  • quick_queue            │  │  │
                                          │  │  │  • long_queue             │  │  │
                                          │  │  │  • dead_letter_queue      │  │  │
                                          │  │  └───────────────────────────┘  │  │
                                          │  └─────────────────────────────────┘  │
                                          └───────────────────────────────────────┘
                                                             │
                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                     │
│                                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  OpenAI  │  │  Qdrant  │  │  Slack   │  │  Email   │  │   ...    │        │
│  │   API    │  │  Cloud   │  │   API    │  │  (SMTP)  │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Chat Flow (Fast - Synchronous)

```
User sends message
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Workflow Engine                                │
│                                                 │
│  1. Load agent config from PostgreSQL           │
│  2. Send message + tools to LLM (OpenAI)        │
│  3. LLM decides which tool to call              │
│  4. Execute tool (send email, call API, etc.)   │
│  5. Return response to user                     │
└─────────────────────────────────────────────────┘
       │
       ▼
User receives response (< 30 seconds)
```

### Long Task Flow (Async - Queue + Workers)

```
User: "Generate my Q4 report as PDF"
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Workflow Engine                                │
│                                                 │
│  1. Create job record in PostgreSQL             │
│  2. Queue task to SQS (long_queue)              │
│  3. Return immediately: "Working on it..."      │
└─────────────────────────────────────────────────┘
       │
       ▼
User sees: "Working on it, I'll notify you when ready"

       Meanwhile...

┌─────────────────────────────────────────────────┐
│  Worker (polling SQS)                           │
│                                                 │
│  1. Pick up job from queue                      │
│  2. Generate report (5-10 minutes)              │
│  3. Upload PDF to S3                            │
│  4. Update job status in PostgreSQL             │
│  5. Notify user (webhook, email, or UI poll)    │
└─────────────────────────────────────────────────┘
       │
       ▼
User notified: "Your report is ready! [Download]"
```

---

## Technology Choices

### Why ECS Fargate (Not Kubernetes/EKS)

| Factor | ECS Fargate | EKS (Kubernetes) |
|--------|-------------|------------------|
| **Complexity** | Simple, managed | Complex, requires k8s expertise |
| **Ops overhead** | Minimal | Cluster upgrades, node management |
| **Cost** | Pay per task | Pay for control plane + nodes |
| **Learning curve** | Low | High |
| **Service count** | 2 services + workers | Better suited for 10+ services |

**Recommendation:** ECS Fargate. With 2 backend services and workers, Kubernetes introduces unnecessary complexity. If requirements change, migration to EKS is straightforward since the services are already containerized.

### Why Vercel for Frontend

| Factor | Vercel | ECS Containerized |
|--------|--------|-------------------|
| **Deployment** | Git push = deploy | Build image, push, deploy |
| **PR Previews** | Automatic, free | Manual setup, ~$50/PR |
| **CDN/Edge** | Global, included | Need CloudFront config |
| **Cost** | Free tier / $20/mo | ~$30-50/mo |
| **Next.js optimization** | Built by same team | Manual |

**Recommendation:** Vercel for frontend simplicity. Alternative: AWS Amplify if all-AWS is required.

### Why Queue + Workers (Not Pod-per-Workflow)

| Approach | How It Works | Best For |
|----------|--------------|----------|
| **Queue + Workers** | Long-running workers poll queue, execute tasks | Workflow platforms |
| **Pod per Workflow** | Spawn new container for each execution | CI/CD, untrusted code |

**Why Queue + Workers:**
- **Faster execution** - no container startup overhead (pods take 3-40 seconds to initialize)
- **Lower cost** - workers reuse resources across executions
- **Simpler infrastructure** - no orchestration platform required
- **Industry standard** - used by n8n, Airflow, Zapier, Temporal

### Why SQS for Queues

| Requirement | Solution |
|-------------|----------|
| Quick tasks (< 2 min) | `quick_queue` + workers |
| Long tasks (2+ min) | `long_queue` + workers |
| Failed jobs | Dead Letter Queue (DLQ) |
| Retries | Built-in SQS retry with backoff |

---

## Industry Validation

To validate our architecture choices, we reviewed how established workflow automation platforms handle execution at scale. **All of them use the Queue + Workers pattern**—this is the proven standard for workflow platforms.

### n8n (Open Source Workflow Automation)

> "When running in queue mode, you have multiple n8n instances set up, with one main instance receiving workflow information and the worker instances performing the executions."

**Architecture:** Redis (Bull/BullMQ) + Node.js worker processes

**Source:** [n8n Queue Mode Documentation](https://docs.n8n.io/hosting/scaling/queue-mode/)

### Temporal.io (Used by Netflix, Snap, Datadog)

> "Worker Processes are external to a Temporal Service. The Temporal Service doesn't execute any of your code on Temporal Service machines."

**Architecture:** Task queues + long-running workers

**Source:** [Temporal Documentation](https://docs.temporal.io/workers)

### Apache Airflow (Used by Airbnb, Lyft, Twitter)

> "The workload is distributed on multiple Celery workers which can run on different machines. It is the executor you should use for availability and scalability."

**Architecture:** RabbitMQ/Redis + Celery workers

**Source:** [Airflow Celery Executor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html)

### Zapier (Processes Billions of Tasks)

> "We use RabbitMQ for our message queue... We have roughly 100 workers running background tasks... A simple tech stack with proven technologies is enough for high scalability."

**Architecture:** RabbitMQ + Celery workers (Python/Django backend)

**Source:** [Zapier Engineering Blog - Automating Billions of Tasks](https://zapier.com/engineering/automating-billions-of-tasks/)

### Summary

| Platform | Queue System | Workers | Pod per Execution? |
|----------|--------------|---------|-------------------|
| **n8n** | Redis (Bull/BullMQ) | Node.js processes | No |
| **Temporal** | Internal task queues | Long-running processes | No |
| **Airflow** | RabbitMQ/Redis | Celery workers | No |
| **Zapier** | RabbitMQ | Celery workers (~100+) | No |

**Conclusion:** ElevAIte executes predefined actions (send email, call API, query DB) - not arbitrary user code. The Queue + Workers pattern is the right choice.

---

## Environments

| Environment | Purpose | Deploy Trigger |
|-------------|---------|----------------|
| **Local** | Development | `npm run dev` |
| **Staging** | Integration testing | Auto on merge to `develop` |
| **Production** | Live users | Manual approval |

### PR Previews

| Component | Preview Strategy |
|-----------|------------------|
| **Frontend** | Vercel automatic previews (free) |
| **Backend** | Use staging for testing |

---

## CI/CD Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PR Open   │────▶│   CI Build  │────▶│   Staging   │────▶│ Production  │
│             │     │   & Test    │     │   (auto)    │     │  (manual)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                    │                   │
                    • Lint                • Deploy to           • Requires
                    • Type check            ECS staging           approval
                    • Build images        • Run migrations      • Type "DEPLOY"
                    • Run tests           • Smoke tests           to confirm
```

### Pipeline Stages

**1. On PR (CI)**
- Lint (ESLint, Ruff)
- Type check (TypeScript, Python)
- Build Docker images
- Run unit tests
- Vercel preview for frontend

**2. On Merge to `develop` (Staging)**
- Build and push images to ECR
- Run database migrations
- Deploy to ECS staging
- Run smoke tests

**3. Production (Manual)**
- Requires typing "DEPLOY" to confirm
- Build and push with `prod-` tags
- Run migrations
- Deploy to ECS production
- Notify team

---

## Database Migrations

Migrations run **automatically in the pipeline**, not manually.

```yaml
# In deployment pipeline
- name: Run migrations
  run: alembic upgrade head
```

**Migration safety rules:**
1. Migrations must be backwards compatible
2. Add columns first, deploy code, then remove old columns later
3. Never drop columns in same deploy as code changes

---

## Infrastructure as Code (Terraform)

All infrastructure defined in Terraform:

```
terraform/
├── environments/
│   ├── staging/
│   │   └── main.tf
│   └── production/
│       └── main.tf
├── modules/
│   ├── vpc/           # Network, subnets, security groups
│   ├── ecs/           # ECS cluster, services, workers
│   ├── rds/           # PostgreSQL database
│   ├── sqs/           # Message queues
│   └── s3/            # File storage
└── backend.tf         # S3 state + DynamoDB locking
```

**State management:**
- Terraform state stored in S3
- DynamoDB for state locking (prevents concurrent modifications)

---

## Security

| Layer | Implementation |
|-------|----------------|
| **Network** | VPC with private subnets for data layer |
| **Secrets** | AWS Secrets Manager |
| **Database** | Private subnet, security groups |
| **Encryption** | At rest (RDS, S3) + in transit (TLS) |

---

## Monitoring & Observability

| Component | Tool |
|-----------|------|
| **Infrastructure Metrics** | CloudWatch (CPU, memory, ECS health) |
| **Application Logs** | CloudWatch Logs |
| **Execution Tracking** | PostgreSQL (built into Workflow Engine) |
| **Alerting** | CloudWatch Alarms → Slack |

---

## Cost Estimate (Monthly)

### Staging Environment

| Service | Spec | Est. Cost |
|---------|------|-----------|
| ECS Fargate | 2 services + 1 worker | ~$30-50 |
| RDS Postgres | db.t3.micro | ~$15 |
| Qdrant Cloud | Starter tier | ~$25 |
| S3 | < 10GB | ~$1 |
| SQS | Low volume | ~$1 |
| **Total Staging** | | **~$50-70/mo** |

### Production Environment

| Service | Spec | Est. Cost |
|---------|------|-----------|
| ECS Fargate | 2 services (1 vCPU, 2GB each) | ~$80-100 |
| ECS Workers | 2-5 workers, auto-scaling | ~$50-100 |
| RDS Postgres | db.t3.small, Multi-AZ | ~$50-70 |
| Qdrant Cloud | Standard tier | ~$50-100 |
| S3 | Depends on usage | ~$10-20 |
| SQS | Medium volume | ~$5 |gs
| ALB | 1 load balancer | ~$20 |
| Secrets Manager | ~10 secrets | ~$5 |
| **Total Production** | | **~$250-350/mo** |

### Frontend (Vercel)

| Tier | Cost |
|------|------|
| Free tier | $0 |
| Pro tier | $20/mo per member |

---

## Implementation Phases

### Phase 1: Foundation (Now)
- [x] Local development environment (`docker-compose`)
- [x] CI/CD pipelines (GitHub Actions)
- [ ] Terraform: VPC, ECS cluster, RDS, S3, SQS
- [ ] Deploy staging environment
- [ ] Vercel setup for frontend

### Phase 2: Production Ready
- [ ] Production Terraform environment
- [ ] Secrets Manager integration
- [ ] Monitoring and alerting
- [ ] Auto-scaling for workers

### Phase 3: Scale (As Needed)
- [ ] Add Redis for caching and distributed locks
- [ ] Performance optimization
- [ ] Cost optimization review

---

## Comparison: ECS vs Kubernetes (EKS)

| Aspect | ECS Fargate (Recommended) | Kubernetes (EKS) |
|--------|--------------------------|------------------|
| Monthly cost | ~$300-400 | ~$500-700 (+$75 control plane) |
| Ops complexity | Low | High |
| Team expertise needed | AWS fundamentals | Kubernetes expertise |
| Setup effort | Minimal | Significant |
| Future migration | Straightforward to EKS if needed | N/A |

---

## FAQ

**Q: Why not Kubernetes from the start?**
A: With only 2 services and workers, Kubernetes introduces unnecessary complexity. ECS provides containerization and auto-scaling without the operational overhead.

**Q: What if more isolation is needed later?**
A: EKS can be added for isolated execution if enterprise customers require it. The current architecture supports this evolution.

**Q: How is multi-tenancy handled?**
A: Database-level isolation (tenant_id on all queries). Tenant credentials stored encrypted. No separate infrastructure per tenant required.

**Q: How does this compare to n8n, Airflow, Zapier?**
A: All use the Queue + Workers pattern, which aligns with this recommendation. See Industry Validation section for details.

---

## Appendix: Required AWS Services

| Service | Purpose |
|---------|---------|
| **ECR** | Container Registry - stores Docker images |
| **ECS Fargate** | Runs containers (Auth API, Workflow Engine, Workers) |
| **RDS PostgreSQL** | Primary database |
| **Qdrant Cloud** | Vector database for RAG embeddings (managed, external) |
| **S3** | File storage |
| **SQS** | Message queues |
| **Secrets Manager** | API keys, database credentials |
| **CloudWatch** | Logs, metrics, alerting |
| **ALB** | Application Load Balancer |
| **Route53** | DNS management |
| **ACM** | SSL/TLS certificates |

---