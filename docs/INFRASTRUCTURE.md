# ElevAIte Platform - Infrastructure Architecture

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Overview](#platform-overview)
3. [Platform Components](#platform-components)
   - [Frontend (Next.js on Kubernetes)](#frontend-nextjs-on-kubernetes)
   - [Backend (Python on Kubernetes)](#backend-python-on-kubernetes)
   - [Workers (Python on Kubernetes)](#workers-python-on-kubernetes)
   - [Data Layer](#data-layer)
   - [Vector Database (Qdrant)](#vector-database-qdrant)
4. [Recommended Architecture](#recommended-architecture)
5. [How It Works](#how-it-works)
   - [Chat Flow (Synchronous)](#chat-flow-fast---synchronous)
   - [Long Task Flow (Async)](#long-task-flow-async---queue--workers)
6. [Code Execution Sandbox](#code-execution-sandbox)
   - [Architecture](#architecture)
   - [Security Layers](#security-layers-defense-in-depth)
   - [Pre-Execution Validation](#pre-execution-validation)
   - [API Interface](#api-interface)
   - [Why Not Pod-per-Workflow?](#why-not-pod-per-workflow)
7. [Technology Choices](#technology-choices)
   - [Why Kubernetes](#why-kubernetes)
   - [Why RabbitMQ](#why-rabbitmq-for-queues)
   - [Why MinIO](#why-minio-for-object-storage)
   - [Why Kubernetes for Frontend](#why-kubernetes-for-frontend)
   - [Why Queue + Workers](#why-queue--workers-not-pod-per-workflow)
8. [Industry Validation](#industry-validation)
9. [Environments](#environments)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Database Migrations](#database-migrations)
12. [Infrastructure as Code](#infrastructure-as-code-helm--terraform)
13. [Kubernetes Add-ons](#kubernetes-add-ons-networking--ssl)
14. [Security](#security)
15. [Monitoring & Observability](#monitoring--observability)
16. [Cost Estimate](#cost-estimate-monthly)
17. [Cloud Provider Comparison](#cloud-provider-comparison)
18. [FAQ](#faq)
19. [Appendix](#appendix-required-services)

---

## Executive Summary

This document describes the cloud infrastructure architecture for the ElevAIte AI workflow automation platform. The architecture is **cloud-agnostic, scalable, and portable** - deployable on AWS, Azure, GCP, or self-hosted.

**Key decisions:**
- **Kubernetes** for container orchestration (EKS/AKS/GKE/self-hosted)
- **RabbitMQ** for message queues (cloud-agnostic)
- **MinIO** for object storage (S3-compatible, runs anywhere)
- **Kubernetes** for frontend (containerized Next.js apps)
- **Queue + Workers** pattern for task execution
- **Code Execution Sandbox** for running user/AI-generated code securely
- **Helm Charts** for infrastructure as code

---

## Platform Overview

ElevAIte is an AI workflow automation platform where users:
1. **Build** agents visually in Agent Studio (drag-and-drop nodes)
2. **Deploy** agents to make them available
3. **Interact** via chat interface - agents execute actions (query databases, send emails, call APIs, etc.)

---

## Platform Components

### Frontend (Next.js on Kubernetes)

| App | Port (local) | Purpose |
|-----|--------------|---------|
| **Auth App** | 3000 | Login/signup UI, OAuth flows |
| **ElevAIte App** | 3001 | Agent Studio, chat interface, dashboards |

### Backend (Python on Kubernetes)

| Service | Port | Purpose |
|---------|------|---------|
| **Auth API** | 8004 | Authentication, authorization, user/tenant management |
| **Workflow Engine** | 8006 | Agent execution, chat handling, tool orchestration |
| **Code Execution Service** | 8007 | Sandboxed execution of user/AI-generated code (internal only) |

### Workers (Python on Kubernetes)

| Component | Purpose |
|-----------|---------|
| **Workers** | Consume RabbitMQ queues, execute long-running tasks (report generation, batch processing) |

Workers are the same codebase as Workflow Engine, running in "worker mode" - consuming queues instead of serving HTTP requests.

### Data Layer (Managed Services Only)

All data services are **external managed services** provisioned by Terraform. No databases run in Kubernetes containers.

| Component | Purpose | AWS | Azure | GCP |
|-----------|---------|-----|-------|-----|
| **PostgreSQL** | Primary database - users, tenants, agents, workflows | RDS | Azure Database for PostgreSQL | Cloud SQL |
| **RabbitMQ** | Message queues for async tasks | CloudAMQP / Amazon MQ | CloudAMQP | CloudAMQP |
| **Object Storage** | Uploaded files, generated reports | S3 | Azure Blob Storage | Cloud Storage |
| **Qdrant** | Vector database - document embeddings for RAG | Qdrant Cloud | Qdrant Cloud | Qdrant Cloud |

**Why Managed Services?**
- ✅ Automatic backups and point-in-time recovery
- ✅ Multi-AZ high availability
- ✅ Security patches applied automatically
- ✅ Monitoring and alerting built-in
- ✅ No operational overhead

### Vector Database (Qdrant)

The **Ingestion Service** uses **Qdrant** for storing document embeddings, enabling RAG (Retrieval-Augmented Generation) workflows:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Document     │────▶│    Chunking     │────▶│   Embedding     │────▶│     Qdrant      │
│    Upload       │     │    (Split)      │     │   (OpenAI)      │     │  (Vector Store) │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Ingestion Pipeline Stages:**
1. **PARSING** - Extract text from documents (PDF, DOCX, etc.)
2. **CHUNKING** - Split content into manageable chunks
3. **EMBEDDING** - Generate vector embeddings (OpenAI, Cohere, etc.)
4. **VECTOR_DB** - Store embeddings in Qdrant for similarity search

**Qdrant Deployment:**
| Environment | Deployment | Details |
|-------------|------------|---------|
| Local | Docker container | `docker-compose.dev.yaml` includes `qdrant:6333` |
| Staging | Qdrant Cloud (optional) | `qdrant.enabled: false` by default |
| Production | Qdrant Cloud | `qdrant.enabled: true` with `QDRANT_API_KEY` |

**Alternative Vector DBs Supported:**
- **Pinecone** - Managed cloud service
- **Chroma** - Open-source, self-hosted
- **Qdrant** - Open-source, cloud or self-hosted (recommended)

Configuration in `elevaite_ingestion/config/vector_db_config.py` allows switching between providers.

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    USERS                                        │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      DNS (Route53 / Azure DNS / Cloud DNS)                      │
│                      + Cloudflare (optional CDN/WAF)                            │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER (EKS / AKS / GKE / Self-hosted)                 │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    INGRESS LAYER (nginx-ingress)                          │  │
│  │   cert-manager (auto SSL)    external-dns (auto DNS records)              │  │
│  └─────────────────────────────────────┬─────────────────────────────────────┘  │
│                                        │                                        │
│  ┌─────────────────────────────────────▼─────────────────────────────────────┐  │
│  │                              APPLICATIONS                                 │  │
│  │                                                                           │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│  │   │                          FRONTEND                               │    │  │
│  │   │   ┌───────────────┐            ┌───────────────┐               │    │  │
│  │   │   │   Auth App    │            │ ElevAIte App  │               │    │  │
│  │   │   │   (3000)      │            │    (3001)     │               │    │  │
│  │   │   └───────────────┘            └───────────────┘               │    │  │
│  │   └─────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                           │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│  │   │                          BACKEND                                │    │  │
│  │   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │    │  │
│  │   │   │   Auth API    │  │   Workflow    │  │   Ingestion   │      │    │  │
│  │   │   │    (8004)     │  │    Engine     │  │    Service    │      │    │  │
│  │   │   │               │  │    (8006)     │  │    (8005)     │      │    │  │
│  │   │   └───────────────┘  └───────────────┘  └───────────────┘      │    │  │
│  │   │                                                                 │    │  │
│  │   │   ┌───────────────────────────┐  ┌───────────────────────────┐ │    │  │
│  │   │   │         WORKERS           │  │     Code Exec Svc         │ │    │  │
│  │   │   │  • Consume RabbitMQ       │  │         (8007)            │ │    │  │
│  │   │   │  • Execute workflow steps │  │       [Sandboxed]         │ │    │  │
│  │   │   │  • HPA auto-scaling       │  │                           │ │    │  │
│  │   │   └───────────────────────────┘  └───────────────────────────┘ │    │  │
│  │   └─────────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           OBSERVABILITY                                   │  │
│  │                                                                           │  │
│  │   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐ │  │
│  │   │Prometheus │  │  Grafana  │  │   Loki    │  │    Alertmanager       │ │  │
│  │   │ (metrics) │  │(dashboards)│ │  (logs)   │  │  (alerts → Slack/PD)  │ │  │
│  │   └───────────┘  └───────────┘  └───────────┘  └───────────────────────┘ │  │
│  │                                                                           │  │
│  │   ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │   │  Promtail (log shipping from all pods → Loki)                     │  │  │
│  │   └───────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MANAGED DATA SERVICES (Provisioned by Terraform)             │
│                                                                                 │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐               │
│   │ PostgreSQL │  │  RabbitMQ  │  │   Object   │  │  Qdrant  │               │
│   │ (RDS/Azure │  │ (CloudAMQP │  │  Storage   │  │  Cloud   │               │
│   │  DB/Cloud  │  │/Amazon MQ) │  │ (S3/Blob/  │  │ (Vector) │               │
│   │   SQL)     │  │            │  │   GCS)     │  │          │               │
│   │            │  │            │  │            │  │          │               │
│   └────────────┘  └────────────┘  └────────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                     │
│                                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  OpenAI  │  │  Slack   │  │  Email   │  │ PagerDuty│  │   ...    │         │
│  │   API    │  │   API    │  │  (SMTP)  │  │ (alerts) │  │          │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
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
│  2. Publish task to RabbitMQ (long_queue)       │
│  3. Return immediately: "Working on it..."      │
└─────────────────────────────────────────────────┘
       │
       ▼
User sees: "Working on it, I'll notify you when ready"

       Meanwhile...

┌─────────────────────────────────────────────────┐
│  Worker (consuming RabbitMQ)                    │
│                                                 │
│  1. Pick up job from queue                      │
│  2. Generate report (5-10 minutes)              │
│  3. Upload PDF to MinIO                         │
│  4. Update job status in PostgreSQL             │
│  5. Notify user (webhook, email, or UI poll)    │
└─────────────────────────────────────────────────┘
       │
       ▼
User notified: "Your report is ready! [Download]"
```

---

## Code Execution Sandbox

Agents can execute code in two ways:
1. **AI-generated code** - LLM writes Python to analyze data, perform calculations
2. **User-written code** - Users create custom code blocks in their workflows

Both require secure, isolated execution. We use a **self-hosted sandbox** (no external dependencies).

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Workflow Engine (8006)                                                     │
│                                                                             │
│  • Receives user request                                                    │
│  • Validates and publishes task to RabbitMQ                                 │
│  • Returns immediately: "Working on it..."                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RabbitMQ Queue                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Worker                                                                     │
│                                                                             │
│  Picks up job, executes workflow steps:                                     │
│  • API calls, database queries, email/Slack (trusted operations)            │
│                                                                             │
│  When it hits a "Run Code" node:                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Code Execution Service (8007) - SANDBOXED                           │   │
│  │                                                                      │   │
│  │  • User's custom Python code                                         │   │
│  │  • AI-generated code                                                 │   │
│  │                                                                      │   │
│  │  Isolated with Nsjail:                                               │   │
│  │  • No network access                                                 │   │
│  │  • No filesystem access (except /tmp)                                │   │
│  │  • Memory/CPU/time limits                                            │   │
│  │  • No access to secrets/credentials                                  │   │
│  │  • Syscall filtering (seccomp)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  Continue to next workflow step                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Self-Hosted (Not External Services)

| Factor | Self-Hosted (Nsjail) | External (E2B, Modal) |
|--------|----------------------|----------------------|
| **Cost** | ~$50-100/mo (fixed) | $0.10-0.20/execution (variable) |
| **Dependencies** | None | External service dependency |
| **Latency** | ~10-50ms | ~100-500ms (network round-trip) |
| **Control** | Full | Limited |
| **10K executions/mo** | ~$50-100 | ~$1,000-2,000 |

### Security Layers (Defense in Depth)

```
User writes/AI generates code
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Pre-Execution Validation (in Workflow Engine or Worker)           │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ Static Analysis │  │ Blocklist Check │  │ AI Guardrails (LLM review)  │ │
│  │ (AST parsing)   │  │ (regex patterns)│  │ (~$0.001/review)            │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                              │                                              │
│                        Pass / Reject                                        │
└─────────────────────────────────────────────────────────────────────────────┘
       │
       ▼ (only if passed, queued to RabbitMQ, picked up by Worker)
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: Kubernetes Pod Isolation (automatic)                              │
│  • Namespace isolation                                                      │
│  • Network policies                                                         │
│  • Resource quotas                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
       │
       ▼ (Worker calls Code Execution Service)
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: Nsjail Process Sandbox (in Code Execution Service)                │
│  • Linux namespaces (PID, network, mount, user)                             │
│  • seccomp-bpf syscall filtering                                            │
│  • cgroups resource limits                                                  │
│  • Read-only filesystem                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pre-Execution Validation

Before code reaches the sandbox, we validate it:

**1. Static Analysis (Free, Instant)**
- Parse code with Python AST
- Block dangerous imports: `os`, `subprocess`, `socket`, `requests`
- Block dangerous functions: `eval`, `exec`, `compile`, `open`

**2. Blocklist Patterns (Free, Instant)**
- Regex patterns for known bad code
- `__globals__`, `__class__`, dunder method access
- Shell command patterns

**3. AI Guardrails (Optional, ~$0.001/review)**
- LLM reviews code for malicious intent
- Catches obfuscated attacks static analysis misses
- Explains rejection reason to user

### What Users CAN Do

```python
# ALLOWED - Safe data processing
import pandas as pd
import numpy as np
import json

data = json.loads(input_data)
df = pd.DataFrame(data)
result = df.groupby('category').sum()
print(result.to_json())
```

### What Users CANNOT Do

```python
# BLOCKED - No network
import requests
requests.get("https://evil.com")  # ❌ Fails

# BLOCKED - No filesystem
open("/etc/passwd").read()  # ❌ Fails

# BLOCKED - No secrets
import os
os.environ["DATABASE_URL"]  # ❌ Empty

# BLOCKED - No system access
import subprocess
subprocess.run(["rm", "-rf", "/"])  # ❌ Blocked

# BLOCKED - Resource exhaustion
while True: pass  # ❌ Killed after timeout
```

### API Interface

```
POST /execute
{
  "language": "python",
  "code": "import pandas as pd\n...",
  "timeout_seconds": 30,
  "memory_mb": 256,
  "input_data": {"rows": [...]}
}

Response:
{
  "stdout": "Result: 42\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 1523
}
```

### Why Not Pod-per-Workflow?

An alternative approach is spawning a fresh Kubernetes pod for every workflow execution:

| Factor | Pod-per-Workflow | Code Execution Service |
|--------|------------------|------------------------|
| **Startup latency** | 3-30+ seconds | ~10-50ms |
| **User experience** | Slow | Fast |
| **What's isolated** | Everything (overkill) | Only code execution |
| **Infrastructure** | Complex scheduling | Simple service call |
| **Cost** | Higher (pod overhead) | Lower |

**Conclusion:** Most workflow operations (send email, call API, query DB) don't need isolation—they use your trusted code running in Workers. Only arbitrary code execution needs sandboxing. Pod-per-workflow isolates everything unnecessarily.

**Our approach:** Workflow Engine queues → Workers execute trusted operations → Workers call Code Execution Service only for user/AI code.

### Implementation Phases

**Phase 1: MVP** (1-2 weeks)
- Code Execution Service with Docker isolation
- Python support only
- Basic timeout/memory limits
- Integration with Workflow Engine

**Phase 2: Hardening** (1 week)
- Add Nsjail for process-level sandboxing
- Pre-execution validation (static analysis + blocklist)
- AI guardrails integration

**Phase 3: Features** (as needed)
- JavaScript/Node.js support
- File input/output (MinIO integration)
- Additional language support

---

## Technology Choices

### Why Kubernetes

| Factor | Why Kubernetes |
|--------|----------------|
| **Cloud-agnostic** | Runs on AWS (EKS), Azure (AKS), GCP (GKE), or self-hosted |
| **Industry standard** | Largest ecosystem, most tooling |
| **Portability** | Same manifests work everywhere |
| **Auto-scaling** | HPA scales pods based on metrics |
| **Self-healing** | Automatic restarts, health checks |
| **Future-proof** | Enterprise customers often require K8s |

**Managed Kubernetes options:**

| Provider | Service | Notes |
|----------|---------|-------|
| AWS | EKS | + Fargate for serverless pods |
| Azure | AKS | Free control plane |
| GCP | GKE | Autopilot mode available |
| Self-hosted | k3s, kubeadm | For on-prem requirements |

### Why RabbitMQ for Queues

| Factor | RabbitMQ |
|--------|----------|
| **Cloud-agnostic** | Runs anywhere (Docker, K8s, bare metal) |
| **Battle-tested** | Used by Zapier, Instagram, Reddit |
| **Simple** | Push message, consume message - that's it |
| **Management UI** | Built-in web UI at port 15672 |
| **Language support** | First-class Python support (`pika`) |
| **Reliability** | Messages persist to disk, survive restarts |

**Simple usage:**

```python
# Producer - queue a task
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='tasks', durable=True)
channel.basic_publish(exchange='', routing_key='tasks', body='{"job": "generate_report"}')
```

```python
# Consumer - process tasks
def callback(ch, method, properties, body):
    process_job(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='tasks', on_message_callback=callback)
channel.start_consuming()
```

### Why MinIO for Object Storage

| Factor | MinIO |
|--------|-------|
| **S3-compatible** | Same API as AWS S3 - no code changes |
| **Cloud-agnostic** | Runs anywhere |
| **Self-hosted** | No external dependencies |
| **Cost** | Free (open source) |
| **Migration** | Easy switch to native S3/Azure Blob/GCS later |

**Code works with both:**

```python
import boto3

# Works with MinIO OR AWS S3 - just change endpoint
s3 = boto3.client('s3',
    endpoint_url='http://minio:9000',  # MinIO
    # endpoint_url=None,  # AWS S3
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

s3.upload_file('report.pdf', 'reports', 'q4-report.pdf')
```

### Why Kubernetes for Frontend

All components (frontend and backend) run in Kubernetes for:
- **Unified deployment**: Single Helm chart deploys everything
- **Self-contained**: No external dependencies (Vercel, Netlify, etc.)
- **Customer deployment**: Customers deploy the full stack to their own cloud
- **Consistent environment**: Same infrastructure for all environments
Frontend apps (auth-app, elevaite-app) are containerized and deployed alongside backend services.

### Why Queue + Workers (Not Pod-per-Workflow)

| Approach | How It Works | Best For |
|----------|--------------|----------|
| **Queue + Workers** | Long-running workers consume queue, execute tasks | Workflow platforms |
| **Pod per Workflow** | Spawn new container for each execution | CI/CD, untrusted code |

**Why Queue + Workers:**
- **Faster execution** - no container startup overhead (pods take 3-40 seconds to initialize)
- **Lower cost** - workers reuse resources across executions
- **Simpler infrastructure** - standard Deployment, not complex Job scheduling
- **Industry standard** - used by n8n, Airflow, Zapier, Temporal

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

### Environment Strategy

| Environment | Purpose | Deploy Trigger | Data Services |
|-------------|---------|----------------|---------------|
| **Local** | Development | `npm run dev` | Docker Compose (containers) |
| **PR Environments** | PR testing | Auto on PR open | Managed (database-per-PR) |
| **Staging** | Integration testing | Auto on merge to `develop` | Managed (dedicated) |
| **Production** | Live users | Manual approval | Managed (Multi-AZ, HA) |

### Database Strategy (Managed Services Only)

**IMPORTANT:** All environments except local dev use **managed database services**. No databases run in Kubernetes containers.

| Environment | PostgreSQL | RabbitMQ | Why |
|-------------|------------|----------|-----|
| **Production** | RDS Multi-AZ / Cloud SQL / Azure DB | CloudAMQP (dedicated) | HA, automatic backups, security patches |
| **Staging** | RDS Single-AZ / Cloud SQL / Azure DB | CloudAMQP (shared) | Mirror prod, lower cost |
| **PR Envs** | Shared managed DB, **database-per-PR** | Shared instance, **vhost-per-PR** | Fast, isolated, cheap |
| **Local** | Docker Compose | Docker Compose | Fast iteration, offline |

### Database-per-PR Pattern

Each PR gets its own isolated database on a shared managed PostgreSQL instance:

```
Shared Dev Managed PostgreSQL
│
├── elevaite_dev        ← Default dev database
├── pr_123              ← Database for PR #123
├── pr_456              ← Database for PR #456
└── pr_789              ← Database for PR #789
```

**On PR Open:**
```bash
# Automatically run by CI/CD
CREATE DATABASE pr_123;
# Run migrations
uv run alembic upgrade head
```

**On PR Close:**
```bash
# Automatically run by CI/CD
DROP DATABASE pr_123;
```

This pattern:
- ✅ Works with schema-per-tenant multitenancy (tenant schemas inside each PR database)
- ✅ Full isolation between PRs
- ✅ Fast spin-up (no infrastructure provisioning)
- ✅ Cost-effective (shared managed instance)

### PR Previews

| Component | Preview Strategy |
|-----------|------------------|
| **Frontend** | Kubernetes namespace per PR (with backend) |
| **Backend** | Kubernetes namespace per PR with database-per-PR |

---

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PR OPENED/UPDATED                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Lint & Type Check                                                        │
│  2. Build Docker Images (ghcr.io/org/app:pr-123)                            │
│  3. Create PR Database (CREATE DATABASE pr_123)                             │
│  4. Run Migrations (Alembic)                                                │
│  5. Deploy to K8s namespace (pr-123)                                        │
│  6. Comment PR with environment URL                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PR CLOSED/MERGED                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Delete Helm release                                                      │
│  2. Delete K8s namespace (pr-123)                                           │
│  3. Drop PR Database (DROP DATABASE pr_123)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MERGE TO DEVELOP (Staging)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Build & push images (ghcr.io/org/app:staging)                           │
│  2. Get Terraform outputs (database hosts)                                   │
│  3. Deploy to K8s staging namespace (Helm upgrade)                          │
│  4. Run smoke tests                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MERGE TO MAIN (Production)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Build & push images (ghcr.io/org/app:v1.2.3)                            │
│  2. Get Terraform outputs (database hosts)                                   │
│  3. Deploy to K8s production namespace (Helm upgrade --atomic)              │
│  4. Run smoke tests                                                          │
│  5. Auto-rollback on failure                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

**1. On PR Open (PR Environment)**
- Lint (ESLint, Ruff)
- Type check (TypeScript, Python)
- Build Docker images with PR tag
- **Create PR database** (`pr_123`) on shared managed PostgreSQL
- Run migrations
- Deploy to dedicated K8s namespace (`pr-123`)
- Post comment with preview URL

**2. On PR Close (Cleanup)**
- Delete Helm release
- Delete K8s namespace
- **Drop PR database**
- Delete RabbitMQ vhost

**3. On Merge to `develop` (Staging)**
- Build and push images to container registry
- Run database migrations (on staging managed DB)
- Deploy to Kubernetes staging (`helm upgrade`)
- Run smoke tests

**4. On Merge to `main` (Production)**
- Build and push images with version tags
- Run migrations (on production managed DB - Multi-AZ)
- Deploy to Kubernetes production (`helm upgrade --atomic`)
- Auto-rollback on failure
- Create GitHub Release

### GitHub Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | PR push | Lint, test, type-check |
| `pr-environment.yml` | PR open/close | Create/destroy PR environment |
| `deploy-staging.yml` | Push to `develop` | Deploy to staging |
| `deploy-prod.yml` | Push to `main` | Deploy to production |
- Notify team

### Container Registry Options

| Registry | Notes |
|----------|-------|
| **GitHub Container Registry (GHCR)** | Free with GitHub, simple |
| **Docker Hub** | Free tier available |
| **Harbor** | Self-hosted, enterprise features |
| **Cloud-native** | ECR (AWS), ACR (Azure), GCR (GCP) |

---

## Database Migrations

Migrations run **automatically in the pipeline**, not manually.

```yaml
# In Helm chart or deployment pipeline
initContainers:
  - name: migrations
    image: elevaite-api:latest
    command: ["alembic", "upgrade", "head"]
```

**Migration safety rules:**
1. Migrations must be backwards compatible
2. Add columns first, deploy code, then remove old columns later
3. Never drop columns in same deploy as code changes

---

## Infrastructure as Code (Helm + Terraform)

### Helm Charts (Kubernetes resources)

Helm charts deploy **application services only** (no databases in containers).

```
helm/
├── elevaite/
│   ├── Chart.yaml
│   ├── values.yaml              # External DB configs, application defaults
│   ├── values-staging.yaml      # Staging overrides
│   ├── values-production.yaml   # Production overrides
│   ├── values-pr.yaml           # PR environment overrides
│   └── templates/
│       ├── auth-api-deployment.yaml
│       ├── workflow-engine-deployment.yaml
│       ├── ingestion-deployment.yaml
│       ├── worker-deployment.yaml
│       ├── code-execution-deployment.yaml
│       ├── ingress.yaml
│       ├── serviceaccount.yaml
│       └── secrets.yaml
└── monitoring/                  # Optional: deploy Prometheus/Grafana
```

**Key Helm Values:**
```yaml
# values.yaml - External databases only
postgresql:
  host: ""              # Set from Terraform output
  port: 5432
  database: "elevaite"
  existingSecret: "elevaite-db-credentials"

rabbitmq:
  host: ""              # Set from Terraform output
  port: 5672
  existingSecret: "elevaite-rabbitmq-credentials"
```

### Terraform (Cloud Infrastructure)

Terraform provisions **all managed services** (databases, queues, storage, Kubernetes clusters).

```
terraform/
├── README.md                    # Usage documentation
├── modules/                     # Reusable multi-cloud modules
│   ├── database/                # PostgreSQL (RDS/Cloud SQL/Azure DB)
│   │   └── main.tf              # Supports AWS, Azure, GCP
│   ├── rabbitmq/                # RabbitMQ (CloudAMQP or Amazon MQ)
│   │   └── main.tf
│   ├── storage/                 # Object storage (S3/GCS/Azure Blob)
│   │   └── main.tf
│   ├── kubernetes/              # K8s clusters (EKS/GKE/AKS)
│   │   └── main.tf
│   ├── dns/                     # DNS zones (Route53/Azure DNS/Cloud DNS)
│   │   └── main.tf
│   ├── cluster-addons/          # K8s add-ons (ingress, cert-manager, external-dns)
│   │   └── main.tf
│   └── monitoring/              # Observability (Prometheus, Grafana, Loki)
│       └── main.tf
│
├── environments/                # Environment-specific configs
│   ├── dev/                     # Shared dev (for PR environments)
│   │   ├── aws/main.tf
│   │   ├── azure/main.tf
│   │   └── gcp/main.tf
│   ├── staging/
│   │   ├── aws/main.tf
│   │   ├── azure/main.tf
│   │   └── gcp/main.tf
│   └── production/
│       ├── aws/main.tf
│       ├── azure/main.tf
│       └── gcp/main.tf
│
└── scripts/                     # Helper scripts
    ├── create-pr-database.sh    # Create database for PR
    └── destroy-pr-database.sh   # Drop PR database on close
```

### Terraform Multi-Cloud Modules

Each module supports all three major cloud providers:

```hcl
# Example: terraform/modules/database/main.tf
variable "cloud_provider" {
  description = "Cloud provider: aws, azure, or gcp"
  type        = string
}

# AWS RDS
resource "aws_db_instance" "postgres" {
  count = var.cloud_provider == "aws" ? 1 : 0
  # ...
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "postgres" {
  count = var.cloud_provider == "azure" ? 1 : 0
  # ...
}

# Google Cloud SQL
resource "google_sql_database_instance" "postgres" {
  count = var.cloud_provider == "gcp" ? 1 : 0
  # ...
}
```

### Provisioning Flow

```
1. Choose cloud provider (AWS/Azure/GCP)
2. Run Terraform to provision managed services
3. Get outputs (database hosts, etc.)
4. Deploy apps with Helm using those outputs
```

```bash
# Deploy to staging on AWS
cd terraform/environments/staging/aws
terraform init
terraform apply

# Get outputs and deploy with Helm
terraform output -json > outputs.json
helm upgrade --install elevaite ./helm/elevaite \
  --values ./helm/elevaite/values-staging.yaml \
  --set postgresql.host=$(terraform output -raw database_host)
```

---

## Kubernetes Add-ons (Networking & SSL)

The `cluster-addons` Terraform module deploys essential Kubernetes add-ons for traffic routing, SSL, and DNS management.

### Components Deployed

| Component | Purpose | Terraform Module |
|-----------|---------|------------------|
| **nginx-ingress** | Routes external traffic to services | `cluster-addons` |
| **cert-manager** | Automatic SSL certificate provisioning | `cluster-addons` |
| **external-dns** | Automatic DNS record creation | `cluster-addons` |

### nginx-ingress Controller

Routes all external HTTP/HTTPS traffic to the appropriate service:

```
User → DNS → Load Balancer → nginx-ingress → Service (Auth API, Frontend, etc.)
```

- Deployed via Helm chart (`ingress-nginx`)
- Creates cloud-provider Load Balancer (NLB on AWS, Azure LB, GCP LB)
- Supports annotations for SSL redirect, rate limiting, etc.

### cert-manager

Automatically provisions and renews SSL certificates from Let's Encrypt:

```
Ingress created → cert-manager sees annotation → Requests cert → Stores in Secret → nginx uses it
```

- **letsencrypt-staging**: For testing (fake certs, no rate limits)
- **letsencrypt-prod**: For production (real certs, rate limited)

### external-dns

Automatically creates DNS records when Ingress resources are created:

```
Ingress with host: app.elevaite.ai → external-dns → Creates A record in Route53/Azure DNS/Cloud DNS
```

| Cloud | DNS Provider |
|-------|--------------|
| AWS | Route53 |
| Azure | Azure DNS |
| GCP | Cloud DNS |

### DNS Module

The `dns` Terraform module provisions DNS zones:

```hcl
# terraform/modules/dns/main.tf
# Provisions:
# - Main zone (elevaite.ai)
# - Dev zone for PR environments (dev.elevaite.ai → pr-123.dev.elevaite.ai)
```

---

## Security

| Layer | Implementation |
|-------|----------------|
| **Network** | Kubernetes Network Policies, private subnets |
| **Secrets** | Kubernetes Secrets + Sealed Secrets (encrypted in Git) |
| **Database** | Private network, TLS connections |
| **Encryption** | At rest (volume encryption) + in transit (TLS) |
| **RBAC** | Kubernetes RBAC for service accounts |

### Secrets Management Options

| Option | Pros | Cons |
|--------|------|------|
| **K8s Secrets + Sealed Secrets** | Simple, GitOps-friendly | Basic |
| **HashiCorp Vault** | Enterprise-grade, dynamic secrets | Complex |
| **External Secrets Operator** | Syncs from cloud providers | Cloud dependency |

**Recommendation:** Start with K8s Secrets + Sealed Secrets. Add Vault later if needed.

---

## Monitoring & Observability

All monitoring tools are deployed via Terraform's `monitoring` module using Helm charts.

| Component | Tool | Purpose | Cloud-Agnostic |
|-----------|------|---------|----------------|
| **Metrics** | Prometheus | Collects metrics from all pods/services | ✅ |
| **Dashboards** | Grafana | Visualization, pre-built K8s dashboards | ✅ |
| **Log Collection** | Promtail | Ships logs from all pods to Loki | ✅ |
| **Log Aggregation** | Loki | Stores and queries logs | ✅ |
| **Alerting** | Alertmanager | Routes alerts to Slack/PagerDuty | ✅ |
| **Tracing** | Jaeger (optional) | Distributed tracing | ✅ |

### Deployed by Terraform

```yaml
# terraform/modules/monitoring/main.tf deploys:
- Prometheus (kube-prometheus-stack)
  - Prometheus server
  - Alertmanager
  - Node Exporter
  - Kube State Metrics
- Grafana (with pre-configured dashboards)
- Loki (log aggregation)
- Promtail (log shipping)
```

### Alert Routing

| Severity | Destination | When |
|----------|-------------|------|
| **Critical** | PagerDuty | Production only |
| **Warning** | Slack | All environments |
| **Info** | Grafana | Dashboard only |

All tools run in Kubernetes, no cloud vendor lock-in.

---

## Cost Estimate (Monthly)

### Per-Environment Cost (Staging OR Production)

**Note:** Both staging and production now use identical minimal resources for initial deployment. Scale up production later based on actual usage.

#### AWS (EKS)

| Service | Spec | Est. Cost |
|---------|------|-----------|
| EKS control plane | | ~$75 |
| EC2 nodes | 2x t3.small | ~$30 |
| RDS PostgreSQL | db.t4g.micro, single-AZ | ~$15 |
| NAT Gateway | Single gateway | ~$30 |
| CloudAMQP | Free tier (lemur) | $0 |
| S3 storage | Standard | ~$5 |
| **Total per environment** | | **~$155/mo** |

#### Azure (AKS)

| Service | Spec | Est. Cost |
|---------|------|-----------|
| AKS control plane | | $0 (free) |
| VM nodes | 2x Standard_B2s | ~$60 |
| Azure Database for PostgreSQL | B_Gen5_1, single-zone | ~$20 |
| CloudAMQP | Free tier (lemur) | $0 |
| Blob Storage | LRS | ~$5 |
| Load Balancer | Standard | ~$15 |
| **Total per environment** | | **~$100/mo** |

#### GCP (GKE)

| Service | Spec | Est. Cost |
|---------|------|-----------|
| GKE control plane | Zonal cluster | $0 (free) |
| Compute nodes | 2x e2-micro | ~$60 |
| Cloud SQL | db-f1-micro, single-zone | ~$20 |
| CloudAMQP | Free tier (lemur) | $0 |
| Cloud Storage | Standard | ~$5 |
| Load Balancer | Standard | ~$15 |
| **Total per environment** | | **~$100/mo** |

### Cloud Provider Comparison

| Provider | K8s Control Plane | Per-Environment Total | Notes |
|----------|-------------------|----------------------|--------|
| **AWS (EKS)** | $75/mo | **~$155/mo** | EKS control plane cost is fixed |
| **Azure (AKS)** | Free | **~$100/mo** | Free control plane saves cost |
| **GCP (GKE)** | Free (zonal) | **~$100/mo** | Free zonal control plane |
| **Self-hosted (k3s)** | Free | ~$85/mo + ops | No control plane costs |

### Scaling Up for Production

When your production environment needs more resources:
- **Database:** Upgrade to larger instance, enable Multi-AZ (~$50-150/mo additional)
- **Kubernetes:** Add nodes, upgrade to larger instances (~$100-300/mo additional)
- **RabbitMQ:** Upgrade to dedicated plan (~$30-50/mo additional)
- **Monitoring:** Increase retention, add external storage (~$30-50/mo additional)

### Frontend (Kubernetes)

| Setup | Cost |
|-------|------|
| Included in K8s cluster | $0 additional |
| Resource allocation | ~0.5 vCPU, 512MB per app |

---

## Cloud Provider Comparison

| Aspect | AWS | Azure | GCP | Self-hosted |
|--------|-----|-------|-----|-------------|
| **Kubernetes** | EKS ($75/mo control plane) | AKS (free control plane) | GKE (free control plane) | k3s/kubeadm |
| **Managed Postgres** | RDS | Azure Database | Cloud SQL | Self-managed |
| **Object Storage** | S3 | Blob Storage | Cloud Storage | MinIO |
| **Container Registry** | ECR | ACR | GCR | Harbor/GHCR |
| **Load Balancer** | ALB | Azure LB | Cloud LB | nginx/traefik |

**Recommendation:** Start with Azure (AKS) or GCP (GKE) for free control plane. AWS if team already has expertise.

---

## FAQ

**Q: Why Kubernetes instead of simpler options?**
A: Cloud-agnostic requirement. Kubernetes runs everywhere (AWS/Azure/GCP/on-prem). The complexity is worth the portability for enterprise customers.

**Q: Why RabbitMQ instead of managed queues (SQS, Azure Queue)?**
A: Cloud-agnostic requirement. RabbitMQ runs anywhere with the same code. No vendor lock-in.

**Q: Why MinIO instead of native object storage?**
A: S3-compatible API means same code works everywhere. Can switch to native S3/Blob/GCS later with zero code changes.

**Q: How is multi-tenancy handled?**
A: Database-level isolation (tenant_id on all queries). Tenant credentials stored encrypted. No separate infrastructure per tenant required.

**Q: How does this compare to n8n, Airflow, Zapier?**
A: All use the Queue + Workers pattern, which aligns with this architecture. See Industry Validation section for details.

**Q: Why not use external code execution services (E2B, Modal)?**
A: Cost and dependency concerns. External services charge per-execution (~$0.10-0.20 each), which adds up quickly. Self-hosted with Nsjail has fixed infrastructure costs regardless of execution volume, and no external dependencies.

**Q: How is user/AI-generated code secured?**
A: Three-layer defense: (1) Pre-execution validation with static analysis, blocklist patterns, and optional AI review; (2) Kubernetes pod isolation with network policies; (3) Nsjail process sandbox with no network, limited filesystem, resource limits, and syscall filtering.

**Q: Can we switch cloud providers later?**
A: Yes! That's the point of cloud-agnostic design. Kubernetes manifests, RabbitMQ, MinIO, and PostgreSQL all work identically across providers.

---

## Appendix: Required Services

### Infrastructure Services (Provisioned by Terraform)

| Service | Purpose | Terraform Module | AWS | Azure | GCP |
|---------|---------|------------------|-----|-------|-----|
| **Kubernetes** | Container orchestration | `kubernetes` | EKS | AKS | GKE |
| **PostgreSQL** | Primary database | `database` | RDS | Azure Database | Cloud SQL |
| **RabbitMQ** | Message queues | `rabbitmq` | CloudAMQP/Amazon MQ | CloudAMQP | CloudAMQP |
| **Object Storage** | File storage (S3-compatible) | `storage` | S3 | Azure Blob | Cloud Storage |
| **Qdrant** | Vector database | External | Qdrant Cloud | Qdrant Cloud | Qdrant Cloud |
| **DNS** | Domain management | `dns` | Route53 | Azure DNS | Cloud DNS |

### Kubernetes Add-ons (Deployed by Terraform)

| Service | Purpose | Terraform Module | Helm Chart |
|---------|---------|------------------|------------|
| **nginx-ingress** | HTTP/HTTPS routing | `cluster-addons` | ingress-nginx |
| **cert-manager** | Automatic SSL certificates | `cluster-addons` | cert-manager |
| **external-dns** | Automatic DNS records | `cluster-addons` | external-dns |

### Monitoring Stack (Deployed by Terraform)

| Service | Purpose | Terraform Module | Helm Chart |
|---------|---------|------------------|------------|
| **Prometheus** | Metrics collection | `monitoring` | kube-prometheus-stack |
| **Grafana** | Dashboards, visualization | `monitoring` | kube-prometheus-stack |
| **Alertmanager** | Alert routing (Slack/PagerDuty) | `monitoring` | kube-prometheus-stack |
| **Loki** | Log aggregation | `monitoring` | loki |
| **Promtail** | Log shipping to Loki | `monitoring` | promtail |

---

## Appendix: Local Development (docker-compose.dev.yaml)

```yaml
services:
  # Infrastructure
  postgres:
    image: postgres:15-alpine
    ports:
      - "5433:5432"
    environment:
      POSTGRES_USER: elevaite
      POSTGRES_PASSWORD: elevaite

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: elevaite
      RABBITMQ_DEFAULT_PASS: elevaite

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"  # Console
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"

  # Backend Services
  auth-api:
    build:
      context: .
      dockerfile: python_apps/auth_api/Dockerfile
    ports:
      - "8004:8004"
    environment:
      DATABASE_URL: postgresql://elevaite:elevaite@postgres:5432/auth

  workflow-engine:
    build:
      context: .
      dockerfile: python_apps/workflow-engine-poc/Dockerfile
    ports:
      - "8006:8006"
    environment:
      DATABASE_URL: postgresql://elevaite:elevaite@postgres:5432/workflow
      RABBITMQ_URL: amqp://elevaite:elevaite@rabbitmq:5672/
      MINIO_ENDPOINT: minio:9000

  worker:
    build:
      context: .
      dockerfile: python_apps/workflow-engine-poc/Dockerfile
    command: ["python", "-m", "workflow_engine_poc.worker"]
    environment:
      DATABASE_URL: postgresql://elevaite:elevaite@postgres:5432/workflow
      RABBITMQ_URL: amqp://elevaite:elevaite@rabbitmq:5672/
      MINIO_ENDPOINT: minio:9000
      CODE_EXECUTION_URL: http://code-execution:8007

  code-execution:
    build:
      context: .
      dockerfile: python_apps/code_execution/Dockerfile
    ports:
      - "8007:8007"
    privileged: true  # Required for Nsjail
```

---

## Appendix: Example Helm Values

```yaml
# values-production.yaml
replicaCount:
  authApi: 2
  workflowEngine: 3
  worker: 5
  codeExecution: 2

resources:
  authApi:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  worker:
    requests:
      cpu: 1000m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 2Gi

autoscaling:
  worker:
    enabled: true
    minReplicas: 2
    maxReplicas: 20
    targetCPUUtilization: 70

rabbitmq:
  replicaCount: 3
  persistence:
    size: 10Gi

postgresql:
  # Use external managed database in production
  enabled: false
  external:
    host: your-postgres.region.rds.amazonaws.com
    database: elevaite

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.elevaite.ai
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: elevaite-tls
      hosts:
        - api.elevaite.ai
```

---
