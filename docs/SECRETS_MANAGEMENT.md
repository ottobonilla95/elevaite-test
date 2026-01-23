# Secrets Management Guide

This guide explains how to manage secrets (API keys, passwords, certificates) in the ElevAIte platform across different environments.

## Table of Contents

- [Overview](#overview)
- [Required Secrets](#required-secrets)
- [Local Development](#local-development)
- [Staging & Production](#staging--production)
  - [AWS Secrets Manager](#aws-secrets-manager)
  - [Azure Key Vault](#azure-key-vault)
  - [Google Secret Manager](#google-secret-manager)
- [Kubernetes Integration](#kubernetes-integration)
- [CI/CD Pipeline](#cicd-pipeline)
- [Secret Rotation](#secret-rotation)
- [Best Practices](#best-practices)

---

## Overview

ElevAIte uses different secret management strategies per environment:

| Environment | Secret Storage | Integration Method |
|-------------|---------------|-------------------|
| **Local** | `.env` file | Direct environment variables |
| **Staging** | Cloud Secrets Manager | Kubernetes External Secrets |
| **Production** | Cloud Secrets Manager | Kubernetes External Secrets |

---

## Required Secrets

### Application Secrets

| Secret Name | Description | Required For | Example Value |
|-------------|-------------|--------------|---------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls | workflow-engine | `sk-...` |
| `GEMINI_API_KEY` | Google Gemini API key | workflow-engine | `AI...` |
| `GOOGLE_CLIENT_ID` | OAuth client ID | auth-api | `123...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | auth-api | `GOCSPX-...` |
| `JWT_SECRET_KEY` | JWT token signing key | auth-api | `random-256-bit-key` |
| `DATABASE_PASSWORD` | PostgreSQL password | all services | `strong-password` |
| `QDRANT_API_KEY` | Qdrant Cloud API key | ingestion, workflow-engine | `qdrant-...` |

### Infrastructure Secrets

| Secret Name | Description | Required For | Example Value |
|-------------|-------------|--------------|---------------|
| `rabbitmq-password` | RabbitMQ password | all services | `random-password` |
| `minio-root-password` | MinIO root password | ingestion | `random-password` |
| `postgres-password` | PostgreSQL admin password | all services | `strong-password` |
| `grafana-admin-password` | Grafana dashboard password | monitoring | `random-password` |

### Third-Party Integration Secrets

| Secret Name | Description | Required For | Example Value |
|-------------|-------------|--------------|---------------|
| `slack-webhook-url` | Slack notifications webhook | workflow-engine | `https://hooks.slack.com/...` |
| `github-token` | GitHub API token | CI/CD | `ghp_...` |
| `docker-hub-token` | Docker Hub registry token | CI/CD | `dckr_...` |

---

## Local Development

### Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your local secrets:
   ```bash
   # .env
   OPENAI_API_KEY=sk-your-key-here
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Never commit `.env` to git** - it's in `.gitignore`

### Secret Generation

Generate strong secrets locally:

```bash
# JWT secret (256-bit)
openssl rand -hex 32

# Database password
openssl rand -base64 24

# Generic secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Staging & Production

### AWS Secrets Manager

#### 1. Create Secrets

```bash
# Application secrets
aws secretsmanager create-secret \
  --name /elevaite/staging/openai-api-key \
  --secret-string "sk-your-key-here" \
  --region us-east-1

aws secretsmanager create-secret \
  --name /elevaite/staging/google-oauth \
  --secret-string '{
    "client_id": "your-id.apps.googleusercontent.com",
    "client_secret": "GOCSPX-your-secret"
  }' \
  --region us-east-1

# Database password
aws secretsmanager create-secret \
  --name /elevaite/staging/database-password \
  --secret-string "$(openssl rand -base64 24)" \
  --region us-east-1

# JWT secret
aws secretsmanager create-secret \
  --name /elevaite/staging/jwt-secret \
  --secret-string "$(openssl rand -hex 32)" \
  --region us-east-1
```

#### 2. Grant IAM Permissions

```hcl
# terraform/modules/eks-irsa/secrets-policy.tf
resource "aws_iam_policy" "secrets_access" {
  name = "elevaite-secrets-access-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:/elevaite/${var.environment}/*"
        ]
      }
    ]
  })
}
```

---

### Azure Key Vault

#### 1. Create Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name elevaite-staging \
  --resource-group elevaite-staging \
  --location eastus

# Add secrets
az keyvault secret set \
  --vault-name elevaite-staging \
  --name openai-api-key \
  --value "sk-your-key-here"

az keyvault secret set \
  --vault-name elevaite-staging \
  --name google-client-id \
  --value "your-id.apps.googleusercontent.com"

az keyvault secret set \
  --vault-name elevaite-staging \
  --name google-client-secret \
  --value "GOCSPX-your-secret"
```

#### 2. Grant AKS Access

```bash
# Get AKS managed identity
AKS_IDENTITY=$(az aks show \
  --resource-group elevaite-staging \
  --name elevaite-staging \
  --query identityProfile.kubeletidentity.clientId \
  --output tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name elevaite-staging \
  --object-id $AKS_IDENTITY \
  --secret-permissions get list
```

---

### Google Secret Manager

#### 1. Create Secrets

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "sk-your-key-here" | \
  gcloud secrets create openai-api-key \
  --data-file=- \
  --replication-policy="automatic"

echo -n "your-id.apps.googleusercontent.com" | \
  gcloud secrets create google-client-id \
  --data-file=- \
  --replication-policy="automatic"

echo -n "GOCSPX-your-secret" | \
  gcloud secrets create google-client-secret \
  --data-file=- \
  --replication-policy="automatic"
```

#### 2. Grant GKE Access

```bash
# Get GKE service account
GKE_SA=$(gcloud container clusters describe elevaite-staging \
  --region us-central1 \
  --format='value(nodeConfig.serviceAccount)')

# Grant access to secrets
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${GKE_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding google-client-id \
  --member="serviceAccount:${GKE_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Kubernetes Integration

### Option 1: External Secrets Operator (Recommended)

#### Install Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace
```

#### Configure Secret Store

**AWS:**
```yaml
# k8s/external-secrets/aws-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: default
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

**Azure:**
```yaml
# k8s/external-secrets/azure-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-key-vault
  namespace: default
spec:
  provider:
    azurekv:
      vaultUrl: "https://elevaite-staging.vault.azure.net"
      authType: WorkloadIdentity
      serviceAccountRef:
        name: external-secrets-sa
```

**GCP:**
```yaml
# k8s/external-secrets/gcp-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-manager
  namespace: default
spec:
  provider:
    gcpsm:
      projectID: "your-project-id"
      auth:
        workloadIdentity:
          serviceAccountRef:
            name: external-secrets-sa
```

#### Create External Secret

```yaml
# k8s/external-secrets/app-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager  # or azure-key-vault / gcp-secret-manager
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
    - secretKey: OPENAI_API_KEY
      remoteRef:
        key: /elevaite/staging/openai-api-key
    - secretKey: GOOGLE_CLIENT_ID
      remoteRef:
        key: /elevaite/staging/google-oauth
        property: client_id
    - secretKey: GOOGLE_CLIENT_SECRET
      remoteRef:
        key: /elevaite/staging/google-oauth
        property: client_secret
```

### Option 2: Manual Kubernetes Secrets

```bash
# Create secret manually
kubectl create secret generic app-secrets \
  --from-literal=OPENAI_API_KEY='sk-your-key' \
  --from-literal=GOOGLE_CLIENT_ID='your-id' \
  --from-literal=GOOGLE_CLIENT_SECRET='your-secret' \
  --namespace default
```

### Use Secrets in Pods

```yaml
# helm/elevaite/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-engine
spec:
  template:
    spec:
      containers:
        - name: workflow-engine
          envFrom:
            - secretRef:
                name: app-secrets
          env:
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
```

---

## CI/CD Pipeline

### GitHub Actions Secrets

1. Go to **Settings → Secrets and variables → Actions**
2. Add repository secrets:

| Secret Name | Description |
|-------------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS credentials for Terraform |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AZURE_CREDENTIALS` | Azure service principal JSON |
| `GCP_SA_KEY` | GCP service account key JSON |
| `DOCKER_HUB_USERNAME` | Docker Hub username |
| `DOCKER_HUB_TOKEN` | Docker Hub access token |

### Use in Workflow

```yaml
# .github/workflows/deploy-staging.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to EKS
        run: |
          # Secrets are available as environment variables
          helm upgrade elevaite ./helm/elevaite \
            --set openai.apiKey=${{ secrets.OPENAI_API_KEY }}
```

---

## Secret Rotation

### Automated Rotation (AWS Example)

```python
# scripts/rotate-secrets.py
import boto3
import secrets

def rotate_jwt_secret(secret_name):
    client = boto3.client('secretsmanager')

    # Generate new secret
    new_secret = secrets.token_hex(32)

    # Update in Secrets Manager
    client.update_secret(
        SecretId=secret_name,
        SecretString=new_secret
    )

    # Trigger rolling restart of pods
    # kubectl rollout restart deployment/auth-api

rotate_jwt_secret('/elevaite/production/jwt-secret')
```

### Manual Rotation Checklist

1. **Generate new secret** with same format
2. **Update in secrets manager** (creates new version)
3. **Wait for External Secrets** to sync (check `refreshInterval`)
4. **Restart affected pods** to pick up new values
5. **Verify services** are working correctly
6. **Delete old secret version** after grace period

---

## Best Practices

### ✅ DO

- **Use different secrets per environment** (dev, staging, prod)
- **Rotate secrets regularly** (90 days for production)
- **Grant least-privilege IAM permissions** (only read access, specific paths)
- **Enable audit logging** for secret access
- **Use External Secrets Operator** for Kubernetes integration
- **Store secrets in version control-safe format** (Sealed Secrets for GitOps)
- **Document secret rotation procedures**
- **Test secret rotation** in staging before production

### ❌ DON'T

- **Never commit secrets to git** (use `.gitignore` for `.env`)
- **Don't hardcode secrets** in code or config files
- **Don't share production secrets** via Slack/email/docs
- **Don't use the same secret** across environments
- **Don't log secret values** (even in debug mode)
- **Don't copy secrets** to local machines unnecessarily
- **Don't grant broad IAM permissions** (`secretsmanager:*`)

### Emergency Procedures

#### Secret Leak Response

1. **Immediately revoke** the leaked secret
2. **Rotate** to a new secret value
3. **Audit access logs** for unauthorized usage
4. **Update all affected services** with new secret
5. **Investigate** how the leak occurred
6. **Document incident** for future prevention

#### Lost Access Recovery

1. **Use root/admin credentials** to access secrets manager
2. **Retrieve secret value** from console
3. **Grant access** to new IAM role/service account
4. **Document access** recovery procedure

---

## Troubleshooting

### External Secrets Not Syncing

```bash
# Check External Secrets Operator logs
kubectl logs -n external-secrets-system \
  deployment/external-secrets

# Check ExternalSecret status
kubectl describe externalsecret app-secrets

# Force refresh
kubectl annotate externalsecret app-secrets \
  force-sync=$(date +%s) --overwrite
```

### Permission Denied Errors

```bash
# AWS: Check IAM role permissions
aws iam get-role-policy \
  --role-name external-secrets-role \
  --policy-name secrets-access

# Azure: Check Key Vault access policies
az keyvault show \
  --name elevaite-staging \
  --query properties.accessPolicies

# GCP: Check IAM bindings
gcloud secrets get-iam-policy openai-api-key
```

### Pod Not Getting Secrets

```bash
# Check if secret exists
kubectl get secret app-secrets -o yaml

# Check pod environment variables
kubectl exec -it workflow-engine-xxx -- env | grep OPENAI

# Check ExternalSecret events
kubectl get events --field-selector involvedObject.name=app-secrets
```

---

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [Azure Key Vault Documentation](https://learn.microsoft.com/en-us/azure/key-vault/)
- [Google Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [External Secrets Operator](https://external-secrets.io/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
