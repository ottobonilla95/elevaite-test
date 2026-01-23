# AWS Deployment Guide - ElevAIte Platform

This guide walks you through deploying ElevAIte infrastructure to AWS using Terraform.

## Prerequisites

### 1. AWS Account & Credentials

You need:
- AWS account with admin access
- AWS CLI installed and configured
- Terraform >= 1.0 installed

**Configure AWS CLI:**
```bash
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

**Verify credentials:**
```bash
aws sts get-caller-identity
# Should show your AWS account ID and user
```

### 2. Required Secrets

You'll need these API keys/secrets:

| Secret | Where to Get | Required For |
|--------|--------------|--------------|
| CloudAMQP API Key | https://customer.cloudamqp.com/apikeys | RabbitMQ (message queue) |
| Database Password | Generate secure password | PostgreSQL RDS |
| Grafana Password | Generate secure password | Monitoring dashboard |
| Let's Encrypt Email | Your email address | SSL certificates |
| Slack Webhook (optional) | https://api.slack.com/messaging/webhooks | Alert notifications |

### 3. Domain Name

You need a domain name (e.g., `elevaite.ai`) that you'll configure in Route53.

---

## Step 1: Bootstrap Terraform State Backend (One-Time)

This creates the S3 bucket and DynamoDB table for Terraform state management.

```bash
cd terraform/bootstrap/aws

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Create the state backend
terraform apply
```

**Output will show:**
```
state_bucket_name = "elevaite-terraform-state"
dynamodb_table_name = "elevaite-terraform-locks"
```

✅ **This is done once per AWS account.**

---

## Step 2: Choose Environment

Decide which environment to deploy first. Recommended order:

1. **Staging** - For testing (cheaper resources)
2. **Production** - After validating staging

```bash
# For staging
cd terraform/environments/staging/aws

# For production
cd terraform/environments/production/aws
```

---

## Step 3: Create Secrets File

Create `secrets.auto.tfvars` in your environment directory:

```bash
cd terraform/environments/staging/aws

cat > secrets.auto.tfvars <<'EOF'
# CloudAMQP API Key (get from https://customer.cloudamqp.com/apikeys)
cloudamqp_api_key = "YOUR_CLOUDAMQP_API_KEY"

# Database password (generate a strong password)
db_password = "YOUR_SECURE_DB_PASSWORD"

# Grafana admin password
grafana_admin_password = "YOUR_GRAFANA_PASSWORD"

# Let's Encrypt email (for SSL certificates)
letsencrypt_email = "your-email@example.com"

# Slack webhook URL for alerts (optional)
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
EOF
```

**Generate secure passwords:**
```bash
# Generate random passwords
openssl rand -base64 32  # For db_password
openssl rand -base64 32  # For grafana_admin_password
```

---

## Step 4: Configure Variables (Optional)

If you want to customize settings, create `terraform.tfvars`:

```bash
cat > terraform.tfvars <<'EOF'
# AWS Region (default: us-east-1)
aws_region = "us-east-1"

# Domain name for DNS and SSL
domain_name = "elevaite.ai"
EOF
```

**Default values are already set in main.tf, so this is optional.**

---

## Step 5: Initialize Terraform

```bash
cd terraform/environments/staging/aws

# Download providers and modules
terraform init

# Verify configuration
terraform validate
```

---

## Step 6: Preview Changes

```bash
terraform plan
```

**Review the plan carefully. It will create:**

| Resource | AWS Service | Purpose |
|----------|-------------|---------|
| VPC | Amazon VPC | Network with public/private subnets |
| EKS Cluster | Amazon EKS | Kubernetes cluster (2 nodes) |
| RDS PostgreSQL | Amazon RDS | Database (db.t4g.micro) |
| RabbitMQ | CloudAMQP | Message queue (lemur/free tier) |
| S3 Bucket | Amazon S3 | Object storage |
| Route53 Zone | Amazon Route53 | DNS management |
| Security Groups | EC2 | Network access control |
| Ingress Controller | nginx-ingress | HTTP/HTTPS routing |
| cert-manager | Let's Encrypt | Automatic SSL certificates |
| Monitoring | Prometheus/Grafana | Observability stack |

**Cost estimate:** ~$75-150/month for staging (depends on usage)

---

## Step 7: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

**This will take 15-20 minutes** (EKS cluster creation is slow).

---

## Step 8: Save Outputs

After deployment completes:

```bash
# Save all outputs to a file
terraform output -json > outputs.json

# View specific outputs
terraform output database_host
terraform output rabbitmq_host
terraform output kubernetes_cluster_name
terraform output kubeconfig_command
terraform output grafana_url
```

---

## Step 9: Configure kubectl

Connect to your new Kubernetes cluster:

```bash
# Get the kubeconfig command from outputs
aws eks update-kubeconfig --name elevaite-staging --region us-east-1

# Verify connection
kubectl get nodes

# Should show 2 nodes in Ready state
```

---

## Step 10: Verify Services

Check that all services are running:

```bash
# Check all pods across namespaces
kubectl get pods -A

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check cert-manager
kubectl get pods -n cert-manager

# Check monitoring
kubectl get pods -n monitoring
```

---

## Step 11: Access Grafana

Get Grafana URL and login:

```bash
# Get Grafana URL
terraform output grafana_url
# Output: https://grafana-staging.elevaite.ai

# Login credentials:
# Username: admin
# Password: (value from secrets.auto.tfvars)
```

---

## Step 12: Next Steps - Deploy Application

Now that infrastructure is ready, deploy the ElevAIte application using Helm:

```bash
cd ../../../../helm/elevaite

# Create values file with infrastructure outputs
cat > values-staging-aws.yaml <<EOF
postgresql:
  host: $(cd ../../terraform/environments/staging/aws && terraform output -raw database_host)
  port: 5432
  database: elevaite_staging

rabbitmq:
  host: $(cd ../../terraform/environments/staging/aws && terraform output -raw rabbitmq_host)
  port: 5672

storage:
  bucket: $(cd ../../terraform/environments/staging/aws && terraform output -raw storage_bucket)

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api-staging.elevaite.ai
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-staging-tls
      hosts:
        - api-staging.elevaite.ai
EOF

# Deploy with Helm
helm upgrade --install elevaite . \
  -f values-staging-aws.yaml \
  --namespace elevaite-staging \
  --create-namespace
```

---

## Troubleshooting

### Issue: "error creating S3 bucket: BucketAlreadyExists"

The S3 bucket name is globally unique. Edit `terraform/bootstrap/aws/main.tf`:

```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "elevaite-terraform-state-YOUR-INITIALS-123"  # Make it unique
```

### Issue: "CloudAMQP API key invalid"

1. Go to https://customer.cloudamqp.com/apikeys
2. Create a new API key
3. Update `secrets.auto.tfvars`

### Issue: "EKS cluster not accessible"

Update kubeconfig:
```bash
aws eks update-kubeconfig --name elevaite-staging --region us-east-1
```

### Issue: Pods stuck in "Pending" state

Check node status:
```bash
kubectl get nodes
kubectl describe nodes
```

If nodes aren't ready, check EKS node group:
```bash
aws eks list-nodegroups --cluster-name elevaite-staging
```

### Issue: "Rate limit exceeded" (Let's Encrypt)

Cert-manager might hit Let's Encrypt rate limits. Check:
```bash
kubectl logs -n cert-manager -l app=cert-manager
```

Switch to staging issuer temporarily in `terraform/modules/cluster-addons/main.tf`.

---

## Cleanup / Destroy

**⚠️ WARNING: This will delete everything!**

```bash
cd terraform/environments/staging/aws

# Delete all infrastructure
terraform destroy

# Type 'yes' to confirm
```

**Note:** You cannot easily destroy the bootstrap state bucket due to `prevent_destroy = true`. This is intentional to prevent accidental state loss.

---

## Cost Optimization Tips

**Staging environment:**
- Uses smallest instances (t3.small, db.t4g.micro)
- Single NAT Gateway instead of one per AZ
- No Multi-AZ for RDS
- CloudAMQP free tier

**To reduce costs further:**
1. Stop EKS node group when not in use
2. Use RDS snapshots and delete instance
3. Delete unused S3 objects

---

## Security Checklist

Before going to production:

- [ ] Rotate all default passwords
- [ ] Enable MFA on AWS account
- [ ] Review IAM policies (least privilege)
- [ ] Enable AWS CloudTrail for audit logs
- [ ] Configure VPC Flow Logs
- [ ] Set up AWS Config for compliance
- [ ] Enable RDS automated backups
- [ ] Configure database encryption at rest
- [ ] Set up SNS/PagerDuty for critical alerts
- [ ] Review security groups (no 0.0.0.0/0 in production)

---

## Production Deployment

Once staging is validated:

```bash
# Deploy production (same steps)
cd terraform/environments/production/aws

# Create secrets.auto.tfvars with production secrets
# Review production-specific settings in main.tf

terraform init
terraform plan
terraform apply
```

**Production differences:**
- Larger instances (t3.medium nodes, db.t4g.small RDS)
- Multi-AZ RDS for high availability
- Multiple NAT Gateways (one per AZ)
- 90-day monitoring retention
- PagerDuty integration for critical alerts

---

## Monitoring & Maintenance

**Daily:**
- Check Grafana dashboards for anomalies
- Review CloudWatch alarms

**Weekly:**
- Review AWS billing
- Check RDS backup status
- Update Kubernetes addons

**Monthly:**
- Review AWS Trusted Advisor recommendations
- Update EKS cluster version (if available)
- Rotate access keys and passwords

---

## Support

- **Documentation:** `docs/INFRASTRUCTURE.md`
- **Secrets Management:** `docs/SECRETS_MANAGEMENT.md`
- **Terraform-Helm Integration:** `docs/TERRAFORM_HELM_INTEGRATION.md`

---

## Quick Reference

```bash
# Check Terraform state
terraform state list

# Get specific output
terraform output database_host

# Refresh state
terraform refresh

# View plan without changes
terraform plan -refresh-only

# Update specific module
terraform apply -target=module.database

# Import existing resource
terraform import aws_s3_bucket.example my-bucket-name
```
