# ElevAIte Infrastructure - Terraform

This directory contains all Terraform configurations for provisioning ElevAIte's cloud-agnostic infrastructure.

## 🌐 Multi-Cloud Support

ElevAIte supports deployment to **any** of these cloud providers:
- **AWS** - Amazon Web Services (EKS, RDS, S3)
- **Azure** - Microsoft Azure (AKS, Azure DB, Blob Storage)
- **GCP** - Google Cloud Platform (GKE, Cloud SQL, Cloud Storage)

**Important**: You deploy to ONE cloud provider at a time. Choose your provider and use the corresponding environment configuration.

## 📁 Directory Structure

```
terraform/
├── README.md                    # This file
├── bootstrap/                   # One-time state backend setup
│   ├── aws/                    # S3 + DynamoDB for state locking
│   ├── azure/                  # Azure Storage Account
│   └── gcp/                    # GCS bucket
├── modules/                     # Reusable multi-cloud modules
│   ├── database/               # PostgreSQL (RDS/Azure DB/Cloud SQL)
│   ├── rabbitmq/               # RabbitMQ (CloudAMQP)
│   ├── storage/                # Object Storage (S3/Blob/GCS)
│   ├── kubernetes/             # Kubernetes (EKS/AKS/GKE)
│   ├── dns/                    # DNS (Route53/Azure DNS/Cloud DNS)
│   ├── cluster-addons/         # Ingress, Cert-Manager, External-DNS
│   └── monitoring/             # Prometheus, Grafana, Loki
├── environments/
│   ├── dev/                    # Shared dev (for PR environments)
│   │   ├── aws/
│   │   ├── azure/
│   │   └── gcp/
│   ├── staging/
│   │   ├── aws/
│   │   ├── azure/
│   │   └── gcp/
│   └── production/
│       ├── aws/
│       ├── azure/
│       └── gcp/
└── scripts/
    ├── create-pr-database.sh   # Create database for PR
    └── destroy-pr-database.sh  # Drop database on PR close
```

## 🚀 Quick Start

### 1. Choose Your Cloud Provider

Set your cloud provider (one of: `aws`, `azure`, `gcp`):

```bash
export CLOUD_PROVIDER=aws
```

### 2. Bootstrap State Backend (One-time)

Before using Terraform, set up the state backend:

```bash
# AWS
cd terraform/bootstrap/aws
terraform init
terraform apply

# Azure
cd terraform/bootstrap/azure
terraform init
terraform apply

# GCP
cd terraform/bootstrap/gcp
terraform init
terraform apply
```

### 3. Deploy Infrastructure

```bash
# Development environment (for PR environments)
cd terraform/environments/dev/${CLOUD_PROVIDER}
terraform init
terraform plan
terraform apply

# Staging
cd terraform/environments/staging/${CLOUD_PROVIDER}
terraform init
terraform plan
terraform apply

# Production
cd terraform/environments/production/${CLOUD_PROVIDER}
terraform init
terraform plan
terraform apply
```

## 🔧 Configuration

### Required Variables

Each environment requires these variables (set via `terraform.tfvars` or environment variables):

**AWS:**
```hcl
# terraform.tfvars
aws_region = "us-east-1"
```

**Azure:**
```hcl
# terraform.tfvars
location = "eastus"
```

**GCP:**
```hcl
# terraform.tfvars
project_id = "your-gcp-project-id"
region     = "us-central1"
```

### Sensitive Variables

Create a `secrets.auto.tfvars` file (gitignored):

```hcl
grafana_password = "your-secure-password"
slack_webhook_url = "https://hooks.slack.com/..."
pagerduty_key = "your-pagerduty-key"
```

## 📊 Environments

### Production
- **Purpose**: Live user-facing environment
- **Database**: Managed PostgreSQL with HA, geo-redundant backups
- **Kubernetes**: Multi-node cluster with auto-scaling
- **Monitoring**: Full stack with 90-day retention, alerting enabled

### Staging
- **Purpose**: Pre-production testing
- **Database**: Managed PostgreSQL with HA
- **Kubernetes**: Smaller cluster mirroring production
- **Monitoring**: 15-day retention

### Development
- **Purpose**: Shared infrastructure for PR environments
- **Database**: Single managed instance, databases created per-PR
- **Kubernetes**: Minimal cluster, cost-optimized
- **Monitoring**: 3-day retention, no alerting

## 🔄 PR Environment Pattern

Each pull request gets:
1. **Dedicated database**: `pr_{PR_NUMBER}` in the shared PostgreSQL instance
2. **Dedicated namespace**: `pr-{PR_NUMBER}` in the dev Kubernetes cluster
3. **Isolated vhost**: `/pr_{PR_NUMBER}` in the shared RabbitMQ

```
┌─────────────────────────────────────────────────────────────┐
│                 Shared Dev Infrastructure                    │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL (managed)    │  RabbitMQ (CloudAMQP)            │
│  ├── pr_123 (database)   │  ├── /pr_123 (vhost)            │
│  ├── pr_456 (database)   │  ├── /pr_456 (vhost)            │
│  └── pr_789 (database)   │  └── /pr_789 (vhost)            │
├─────────────────────────────────────────────────────────────┤
│  Kubernetes Cluster                                          │
│  ├── namespace: pr-123                                       │
│  ├── namespace: pr-456                                       │
│  └── namespace: pr-789                                       │
└─────────────────────────────────────────────────────────────┘
```

## 📤 Outputs

After `terraform apply`, these outputs are available:

| Output | Description |
|--------|-------------|
| `database_host` | PostgreSQL endpoint |
| `rabbitmq_host` | RabbitMQ endpoint |
| `storage_bucket` | Object storage bucket name |
| `kubernetes_cluster_name` | K8s cluster name |
| `kubeconfig_command` | Command to configure kubectl |
| `monitoring_grafana_url` | Grafana dashboard URL |

Use in Helm deployments:
```bash
helm upgrade --install elevaite ./helm/elevaite \
  --set postgresql.host=$(terraform output -raw database_host)
```

## 🔐 State Backend Security

### AWS
- S3 bucket with versioning and encryption
- DynamoDB table for state locking
- Bucket policy restricts access

### Azure
- Storage account with blob versioning
- Container for state files
- Managed identity access

### GCP
- GCS bucket with versioning
- Object ACLs for access control

## 🛡️ Security Best Practices

1. **Never commit secrets**: Use `secrets.auto.tfvars` (gitignored)
2. **State encryption**: All backends use server-side encryption
3. **Least privilege**: Service accounts have minimal permissions
4. **Network isolation**: Private endpoints where available
5. **Audit logging**: Cloud provider audit logs enabled

## 🔄 CI/CD Integration

GitHub Actions automatically:
1. Runs `terraform plan` on PRs
2. Runs `terraform apply` for staging (develop branch)
3. Runs `terraform apply` for production (main branch with approval)

The cloud provider is determined by the `CLOUD_PROVIDER` repository variable.

## 📚 Module Reference

### database
Provisions managed PostgreSQL:
- AWS: RDS PostgreSQL
- Azure: Azure Database for PostgreSQL
- GCP: Cloud SQL for PostgreSQL

### rabbitmq
Provisions managed RabbitMQ via CloudAMQP (cloud-agnostic)

### storage
Provisions object storage:
- AWS: S3
- Azure: Blob Storage
- GCP: Cloud Storage

### kubernetes
Provisions managed Kubernetes:
- AWS: EKS
- Azure: AKS
- GCP: GKE

### dns
Provisions DNS zones:
- AWS: Route 53
- Azure: Azure DNS
- GCP: Cloud DNS

### cluster-addons
Deploys Kubernetes add-ons:
- nginx-ingress controller
- cert-manager (Let's Encrypt SSL)
- external-dns (automatic DNS records)

### monitoring
Deploys observability stack:
- Prometheus (metrics)
- Grafana (dashboards)
- Loki (logs)
- Alertmanager (alerts)
