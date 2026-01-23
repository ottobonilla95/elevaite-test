# Terraform-Helm Integration Guide

This guide explains how Terraform infrastructure outputs are passed to Helm charts for application deployment in the ElevAIte platform.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Terraform Outputs](#terraform-outputs)
- [Helm Values Injection](#helm-values-injection)
- [CI/CD Pipeline Integration](#cicd-pipeline-integration)
- [Manual Deployment](#manual-deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

### The Problem

Applications deployed to Kubernetes need to know:
- Database connection strings
- RabbitMQ endpoints
- Storage bucket names
- DNS zone IDs
- Other infrastructure details

### The Solution

**Terraform** provisions infrastructure → **Outputs** connection details → **Helm** injects into application pods

```
┌──────────────┐
│  Terraform   │ Provisions: PostgreSQL, RabbitMQ, S3, etc.
└──────┬───────┘
       │ Outputs: connection strings, endpoints, IDs
       ▼
┌──────────────┐
│ CI/CD Script │ Reads Terraform outputs, generates values.yaml
└──────┬───────┘
       │ helm upgrade --values generated-values.yaml
       ▼
┌──────────────┐
│     Helm     │ Deploys pods with environment variables
└──────────────┘
```

---

## Architecture

### File Structure

```
elevaite/
├── terraform/
│   ├── environments/
│   │   ├── staging/
│   │   │   ├── aws/
│   │   │   │   ├── main.tf
│   │   │   │   └── outputs.tf        # Infrastructure outputs
│   │   │   └── azure/...
│   │   └── production/...
│   └── modules/
│       ├── database/
│       │   └── main.tf                # Module outputs
│       ├── rabbitmq/...
│       └── storage/...
├── helm/
│   └── elevaite/
│       ├── values.yaml                # Default values
│       ├── values-staging.yaml        # Staging overrides
│       ├── values-production.yaml     # Production overrides
│       └── templates/
│           └── deployment.yaml        # Uses {{ .Values.* }}
└── scripts/
    └── deploy.sh                      # Terraform→Helm integration
```

---

## Terraform Outputs

### Module Outputs

Each Terraform module exposes outputs that applications need.

#### Database Module

```hcl
# terraform/modules/database/main.tf
output "host" {
  description = "Database host endpoint"
  value       = aws_db_instance.postgres[0].endpoint
  sensitive   = true
}

output "port" {
  description = "Database port"
  value       = 5432
}

output "database_name" {
  description = "Database name"
  value       = var.database_name
}

output "connection_string" {
  description = "Full connection string (without password)"
  value       = "postgresql://${var.username}@${local.host}:5432/${var.database_name}?sslmode=require"
  sensitive   = false
}
```

#### RabbitMQ Module

```hcl
# terraform/modules/rabbitmq/main.tf
output "host" {
  description = "RabbitMQ host endpoint"
  value       = cloudamqp_instance.rabbitmq[0].host
  sensitive   = true
}

output "port" {
  description = "RabbitMQ AMQP port"
  value       = 5672
}

output "connection_string" {
  description = "RabbitMQ connection URL (without password)"
  value       = "amqp://${var.username}@${local.host}:5672/"
  sensitive   = false
}
```

#### Storage Module

```hcl
# terraform/modules/storage/main.tf
output "bucket_name" {
  description = "Bucket/container name"
  value       = aws_s3_bucket.main[0].bucket
}

output "bucket_arn" {
  description = "Bucket ARN"
  value       = aws_s3_bucket.main[0].arn
}

output "endpoint" {
  description = "S3 endpoint URL"
  value       = "https://s3.${var.region}.amazonaws.com"
}
```

#### Kubernetes Module

```hcl
# terraform/modules/kubernetes/main.tf
output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = aws_eks_cluster.main[0].name
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint"
  value       = aws_eks_cluster.main[0].endpoint
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate"
  value       = base64decode(aws_eks_cluster.main[0].certificate_authority[0].data)
  sensitive   = true
}
```

#### DNS Module

```hcl
# terraform/modules/dns/main.tf
output "zone_id" {
  description = "DNS zone ID"
  value       = aws_route53_zone.main[0].zone_id
}

output "zone_name" {
  description = "DNS zone name"
  value       = var.domain_name
}

output "nameservers" {
  description = "DNS zone nameservers"
  value       = aws_route53_zone.main[0].name_servers
}
```

### Environment Outputs

Environments aggregate module outputs:

```hcl
# terraform/environments/staging/aws/outputs.tf
output "database" {
  description = "Database connection details"
  value = {
    host              = module.database.host
    port              = module.database.port
    database_name     = module.database.database_name
    connection_string = module.database.connection_string
  }
  sensitive = true
}

output "rabbitmq" {
  description = "RabbitMQ connection details"
  value = {
    host              = module.rabbitmq.host
    port              = module.rabbitmq.port
    connection_string = module.rabbitmq.connection_string
  }
  sensitive = true
}

output "storage" {
  description = "Object storage details"
  value = {
    bucket_name = module.storage.bucket_name
    endpoint    = module.storage.endpoint
  }
}

output "kubernetes" {
  description = "Kubernetes cluster details"
  value = {
    cluster_name     = module.kubernetes.cluster_name
    cluster_endpoint = module.kubernetes.cluster_endpoint
  }
}

output "dns" {
  description = "DNS zone details"
  value = {
    zone_id   = module.dns.zone_id
    zone_name = module.dns.zone_name
  }
}
```

---

## Helm Values Injection

### Default Values Template

```yaml
# helm/elevaite/values-staging.yaml
global:
  environment: staging
  cloudProvider: aws
  region: us-west-1

# Infrastructure endpoints (populated by Terraform)
postgresql:
  enabled: false  # Using managed PostgreSQL
  host: ""        # Injected by CI/CD from Terraform output
  port: 5432
  database: workflow_engine
  username: elevaite
  # Password from secrets manager

rabbitmq:
  enabled: false  # Using managed RabbitMQ
  host: ""        # Injected by CI/CD
  port: 5672
  username: elevaite
  # Password from secrets manager

storage:
  type: s3
  bucket: ""      # Injected by CI/CD
  region: us-west-1

qdrant:
  enabled: true
  host: ""        # Manually configured (see Qdrant module README)
  port: 6333

# Application configuration
workflowEngine:
  enabled: true
  replicas: 2
  image:
    repository: elevaite/workflow-engine
    tag: latest
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

authApi:
  enabled: true
  replicas: 2
  image:
    repository: elevaite/auth-api
    tag: latest
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "200m"

ingestion:
  enabled: true
  replicas: 2
  image:
    repository: elevaite/ingestion-service
    tag: latest
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
```

### Deployment Template Using Values

```yaml
# helm/elevaite/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "elevaite.fullname" . }}-workflow-engine
spec:
  replicas: {{ .Values.workflowEngine.replicas }}
  template:
    spec:
      containers:
        - name: workflow-engine
          image: "{{ .Values.workflowEngine.image.repository }}:{{ .Values.workflowEngine.image.tag }}"
          env:
            # Database connection (from Terraform)
            - name: SQLALCHEMY_DATABASE_URL
              value: "postgresql+asyncpg://{{ .Values.postgresql.username }}:$(DATABASE_PASSWORD)@{{ .Values.postgresql.host }}:{{ .Values.postgresql.port }}/{{ .Values.postgresql.database }}"
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password

            # RabbitMQ connection (from Terraform)
            - name: RABBITMQ_URL
              value: "amqp://{{ .Values.rabbitmq.username }}:$(RABBITMQ_PASSWORD)@{{ .Values.rabbitmq.host }}:{{ .Values.rabbitmq.port }}/"
            - name: RABBITMQ_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: rabbitmq-credentials
                  key: password

            # S3 storage (from Terraform)
            - name: STORAGE_BUCKET
              value: {{ .Values.storage.bucket }}
            - name: AWS_REGION
              value: {{ .Values.global.region }}

            # Qdrant (manually configured)
            - name: QDRANT_HOST
              value: {{ .Values.qdrant.host }}
            - name: QDRANT_PORT
              value: {{ .Values.qdrant.port | quote }}
```

---

## CI/CD Pipeline Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
          terraform_wrapper: false  # Important for output parsing

      - name: Get Terraform outputs
        id: terraform
        working-directory: terraform/environments/staging/aws
        run: |
          terraform init
          terraform output -json > outputs.json

          # Extract outputs
          echo "db_host=$(jq -r '.database.value.host' outputs.json)" >> $GITHUB_OUTPUT
          echo "rabbitmq_host=$(jq -r '.rabbitmq.value.host' outputs.json)" >> $GITHUB_OUTPUT
          echo "storage_bucket=$(jq -r '.storage.value.bucket_name' outputs.json)" >> $GITHUB_OUTPUT
          echo "cluster_name=$(jq -r '.kubernetes.value.cluster_name' outputs.json)" >> $GITHUB_OUTPUT

      - name: Configure kubectl
        run: |
          aws eks update-kubeconfig \
            --name ${{ steps.terraform.outputs.cluster_name }} \
            --region us-west-1

      - name: Build and push Docker images
        run: |
          # Build images
          docker build -t elevaite/workflow-engine:${{ github.sha }} \
            -f python_apps/workflow-engine-poc/Dockerfile .

          # Push to registry
          docker push elevaite/workflow-engine:${{ github.sha }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install elevaite ./helm/elevaite \
            --namespace default \
            --values ./helm/elevaite/values-staging.yaml \
            --set postgresql.host=${{ steps.terraform.outputs.db_host }} \
            --set rabbitmq.host=${{ steps.terraform.outputs.rabbitmq_host }} \
            --set storage.bucket=${{ steps.terraform.outputs.storage_bucket }} \
            --set workflowEngine.image.tag=${{ github.sha }} \
            --set authApi.image.tag=${{ github.sha }} \
            --set ingestion.image.tag=${{ github.sha }} \
            --wait \
            --timeout 10m

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/elevaite-workflow-engine
          kubectl rollout status deployment/elevaite-auth-api
          kubectl rollout status deployment/elevaite-ingestion
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh - Deploy with Terraform outputs

set -e

ENVIRONMENT=${1:-staging}
CLOUD_PROVIDER=${2:-aws}
TERRAFORM_DIR="terraform/environments/${ENVIRONMENT}/${CLOUD_PROVIDER}"
HELM_CHART="helm/elevaite"
VALUES_FILE="helm/elevaite/values-${ENVIRONMENT}.yaml"

echo "🚀 Deploying ElevAIte to ${ENVIRONMENT} (${CLOUD_PROVIDER})"

# Step 1: Initialize Terraform
echo "📦 Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init

# Step 2: Get outputs
echo "📊 Reading Terraform outputs..."
terraform output -json > outputs.json

DB_HOST=$(jq -r '.database.value.host' outputs.json)
RABBITMQ_HOST=$(jq -r '.rabbitmq.value.host' outputs.json)
STORAGE_BUCKET=$(jq -r '.storage.value.bucket_name' outputs.json)
CLUSTER_NAME=$(jq -r '.kubernetes.value.cluster_name' outputs.json)
DNS_ZONE=$(jq -r '.dns.value.zone_name' outputs.json)

cd - > /dev/null

# Step 3: Configure kubectl
echo "☸️  Configuring kubectl..."
case "$CLOUD_PROVIDER" in
  aws)
    aws eks update-kubeconfig --name "$CLUSTER_NAME" --region us-west-1
    ;;
  azure)
    az aks get-credentials --resource-group "elevaite-${ENVIRONMENT}" --name "$CLUSTER_NAME"
    ;;
  gcp)
    gcloud container clusters get-credentials "$CLUSTER_NAME" --region us-central1
    ;;
esac

# Step 4: Generate Helm values override
echo "📝 Generating Helm values..."
cat > /tmp/terraform-values.yaml <<EOF
postgresql:
  host: "${DB_HOST}"

rabbitmq:
  host: "${RABBITMQ_HOST}"

storage:
  bucket: "${STORAGE_BUCKET}"

ingress:
  hosts:
    - host: api.${DNS_ZONE}
      paths:
        - path: /
          pathType: Prefix
    - host: app.${DNS_ZONE}
      paths:
        - path: /
          pathType: Prefix

  tls:
    - secretName: elevaite-tls
      hosts:
        - api.${DNS_ZONE}
        - app.${DNS_ZONE}
EOF

# Step 5: Deploy with Helm
echo "🎯 Deploying with Helm..."
helm upgrade --install elevaite "$HELM_CHART" \
  --namespace default \
  --values "$VALUES_FILE" \
  --values /tmp/terraform-values.yaml \
  --wait \
  --timeout 10m

# Step 6: Verify
echo "✅ Verifying deployment..."
kubectl get pods -l app.kubernetes.io/name=elevaite
kubectl get ingress

echo "🎉 Deployment complete!"
echo "📍 Application URL: https://app.${DNS_ZONE}"
echo "📍 API URL: https://api.${DNS_ZONE}"
```

Make the script executable:
```bash
chmod +x scripts/deploy.sh
```

---

## Manual Deployment

### Step-by-Step Process

#### 1. Apply Terraform

```bash
cd terraform/environments/staging/aws
terraform init
terraform apply
```

#### 2. Extract Outputs

```bash
# Get all outputs as JSON
terraform output -json > outputs.json

# Extract specific values
DB_HOST=$(terraform output -raw database_host)
RABBITMQ_HOST=$(terraform output -raw rabbitmq_host)
STORAGE_BUCKET=$(terraform output -raw storage_bucket)
CLUSTER_NAME=$(terraform output -raw kubernetes_cluster_name)
```

#### 3. Configure kubectl

```bash
# AWS
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region us-west-1

# Azure
az aks get-credentials --resource-group elevaite-staging --name "$CLUSTER_NAME"

# GCP
gcloud container clusters get-credentials "$CLUSTER_NAME" --region us-central1
```

#### 4. Create Helm values override

```bash
cat > values-override.yaml <<EOF
postgresql:
  host: "$DB_HOST"

rabbitmq:
  host: "$RABBITMQ_HOST"

storage:
  bucket: "$STORAGE_BUCKET"
EOF
```

#### 5. Deploy with Helm

```bash
helm upgrade --install elevaite ./helm/elevaite \
  --namespace default \
  --values ./helm/elevaite/values-staging.yaml \
  --values values-override.yaml \
  --wait
```

#### 6. Verify

```bash
kubectl get pods
kubectl get svc
kubectl get ingress
kubectl logs -l app=workflow-engine --tail=50
```

---

## Best Practices

### ✅ DO

- **Use Terraform outputs** exclusively for infrastructure details
- **Store outputs as JSON** for easy parsing in CI/CD
- **Validate outputs** before passing to Helm (check not empty)
- **Use Helm value precedence** correctly (base → environment → override)
- **Version your Helm charts** (`Chart.yaml` version field)
- **Test locally** with `helm template` before deploying
- **Use `--wait` flag** in Helm to ensure successful rollout
- **Enable Terraform remote state** for team collaboration

### ❌ DON'T

- **Don't hardcode infrastructure endpoints** in Helm values
- **Don't commit generated values files** to git (`*-override.yaml`)
- **Don't skip `terraform output`** validation
- **Don't use Terraform wrapper** in CI/CD (breaks JSON parsing)
- **Don't expose sensitive outputs** in CI logs (use `sensitive = true`)
- **Don't deploy without terraform plan** review

### Security Considerations

#### Sensitive Outputs

```hcl
# Mark sensitive outputs
output "database_password" {
  value     = random_password.db_password.result
  sensitive = true  # Won't show in terraform output
}
```

#### CI/CD Secret Handling

```yaml
# Mask sensitive outputs in GitHub Actions
- name: Get DB password
  id: db_password
  run: |
    PASSWORD=$(terraform output -raw database_password)
    echo "::add-mask::$PASSWORD"
    echo "password=$PASSWORD" >> $GITHUB_OUTPUT
```

---

## Troubleshooting

### Terraform Output Not Found

**Problem:** `Error: Output value "database_host" not found`

**Solution:**
```bash
# Check available outputs
terraform output

# Ensure outputs.tf exists in environment directory
ls terraform/environments/staging/aws/outputs.tf

# Re-apply if needed
terraform apply -refresh-only
```

### Helm Values Not Applied

**Problem:** Pods still using old/empty values

**Solution:**
```bash
# Check actual rendered values
helm get values elevaite

# Debug template rendering
helm template elevaite ./helm/elevaite \
  --values values-staging.yaml \
  --values values-override.yaml \
  --debug

# Force pod restart
kubectl rollout restart deployment/workflow-engine
```

### kubectl Not Configured

**Problem:** `The connection to the server localhost:8080 was refused`

**Solution:**
```bash
# Verify cluster name
terraform output kubernetes_cluster_name

# Re-configure kubectl
aws eks update-kubeconfig --name <cluster-name> --region us-west-1

# Verify
kubectl cluster-info
```

### Deployment Timeout

**Problem:** `Error: timed out waiting for the condition`

**Solution:**
```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=elevaite

# Check pod logs
kubectl logs <pod-name> --tail=100

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Common issues:
# - Image pull errors → check image tag
# - CrashLoopBackOff → check environment variables
# - Pending → check resource requests/limits
```

---

## References

- [Terraform Outputs Documentation](https://developer.hashicorp.com/terraform/language/values/outputs)
- [Helm Values Documentation](https://helm.sh/docs/chart_template_guide/values_files/)
- [GitHub Actions Terraform Integration](https://github.com/hashicorp/setup-terraform)
- [kubectl Configuration](https://kubernetes.io/docs/tasks/tools/)
