# Pre-Deployment Checklist - AWS

Before starting your AWS deployment, verify you have everything ready.

## ✅ Prerequisites

### 1. AWS Account Access

- [ ] AWS account with admin privileges
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity` works)

### 2. Tools Installed

- [ ] Terraform >= 1.0 (`terraform --version`)
- [ ] kubectl installed (`kubectl version --client`)
- [ ] Helm >= 3.0 (`helm version`)

### 3. Required Accounts & API Keys

| Service | Status | Where to Get |
|---------|--------|--------------|
| CloudAMQP API Key | ⬜ | https://customer.cloudamqp.com/apikeys |
| Let's Encrypt Email | ⬜ | Your email for SSL cert notifications |
| Domain Name | ⬜ | Your domain (e.g., elevaite.ai) |
| Slack Webhook (optional) | ⬜ | https://api.slack.com/messaging/webhooks |

### 4. Cost Understanding

**Environment estimated cost (staging OR production): ~$150/month**

Breakdown (AWS):
- EKS cluster control plane: ~$75/month
- EC2 nodes (2x t3.small): ~$30/month
- RDS PostgreSQL (db.t4g.micro): ~$15/month
- NAT Gateway: ~$30/month
- CloudAMQP (free tier): $0
- S3 storage: ~$5/month
- **Total: ~$155/month per environment**

Breakdown (Azure/GCP):
- AKS/GKE control plane: Free
- Nodes (2x small instances): ~$60/month
- PostgreSQL (Basic tier): ~$20/month
- CloudAMQP (free tier): $0
- Object storage: ~$5/month
- **Total: ~$100/month per environment**

**Note:** Both staging and production use identical minimal resources. Scale up production later when needed based on actual usage.

---

## 📋 Deployment Steps Summary

1. **Bootstrap** (15 min) - Create S3 bucket for Terraform state
2. **Create secrets file** (5 min) - Configure API keys
3. **Deploy infrastructure** (20-30 min) - Terraform apply
4. **Configure kubectl** (2 min) - Connect to cluster
5. **Deploy application** (10 min) - Helm install

**Total time: ~1 hour**

---

## 🔐 Secrets to Prepare

Create these **before** starting:

```bash
# 1. CloudAMQP API Key
# Sign up at https://customer.cloudamqp.com
# Create API key from https://customer.cloudamqp.com/apikeys

# 2. Generate secure passwords
openssl rand -base64 32  # For database
openssl rand -base64 32  # For Grafana

# 3. Have your domain ready
# If using Route53, domain should already be registered
# If using external registrar, be ready to update nameservers

# 4. Let's Encrypt email
# Use a valid email for SSL certificate notifications
```

---

## 🚨 Important Notes

### DNS Configuration

After Terraform creates the Route53 hosted zone, you'll need to:

1. Get the nameservers from Route53
2. Update your domain registrar to use these nameservers
3. Wait for DNS propagation (up to 48 hours, usually 1-2 hours)

**Without DNS working:**
- SSL certificates won't be issued
- External-DNS won't create records
- You'll need to use LoadBalancer IPs directly

### AWS Service Limits

Check your AWS account limits:
```bash
# Check EKS limit
aws service-quotas get-service-quota \
  --service-code eks \
  --quota-code L-1194D53C

# Check VPC limit
aws service-quotas get-service-quota \
  --service-code vpc \
  --quota-code L-F678F1CE
```

### Terraform State

**CRITICAL:** The bootstrap step creates an S3 bucket with `prevent_destroy = true`.

- Never delete this bucket manually
- State file contains sensitive data
- Enable S3 versioning (done automatically)
- Consider enabling S3 bucket logging for audit

---

## 🧪 Test Your Setup

Before running Terraform:

```bash
# 1. Verify AWS access
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/yourname"
# }

# 2. Test CloudAMQP API key
export CLOUDAMQP_API_KEY="your-key-here"
curl -H "Authorization: Bearer $CLOUDAMQP_API_KEY" \
  https://customer.cloudamqp.com/api/instances

# Expected: JSON response with instances (or empty array if none)

# 3. Check AWS region
aws ec2 describe-regions --region us-west-1

# 4. Verify Terraform
terraform version

# 5. Check available EKS versions
aws eks describe-addon-versions --region us-west-1 --query 'addons[0].addonVersions[0].compatibilities[*].clusterVersion' --output table
```

---

## 🎯 Quick Start Command

Once everything above is ready:

```bash
# Full deployment command
cd terraform

# 1. Bootstrap
cd bootstrap/aws
terraform init && terraform apply
cd ../..

# 2. Deploy staging
cd environments/staging/aws

# Create secrets file (edit with your values)
cat > secrets.auto.tfvars <<EOF
cloudamqp_api_key = "YOUR_KEY"
db_password = "$(openssl rand -base64 32)"
grafana_admin_password = "$(openssl rand -base64 32)"
letsencrypt_email = "your-email@example.com"
EOF

# 3. Deploy
terraform init
terraform plan
terraform apply

# 4. Configure kubectl
aws eks update-kubeconfig --name elevaite-staging --region us-west-1

# 5. Verify
kubectl get nodes
kubectl get pods -A
```

---

## 📚 Reference Documents

- [Full Deployment Guide](./AWS_DEPLOYMENT_GUIDE.md)
- [Infrastructure Architecture](../docs/INFRASTRUCTURE.md)
- [Secrets Management](../docs/SECRETS_MANAGEMENT.md)
- [Terraform-Helm Integration](../docs/TERRAFORM_HELM_INTEGRATION.md)

---

## ⚠️ Common Gotchas

1. **S3 bucket name conflicts** - Bucket names are globally unique. If `elevaite-terraform-state` is taken, add a suffix.

2. **CloudAMQP regions** - Use format `amazon-web-services::us-west-1` not just `us-west-1`.

3. **EKS creation is slow** - Takes 15-20 minutes. Don't interrupt it.

4. **DNS propagation** - SSL certs won't work until DNS is set up.

5. **kubectl context** - After deploy, run `aws eks update-kubeconfig` to connect.

6. **Cost surprises** - NAT Gateway costs $0.045/hour (~$32/month) even if unused.

7. **Bootstrap prevent_destroy** - You can't easily destroy the state bucket. This is by design.

---

## 🆘 If Something Goes Wrong

### Terraform apply fails

```bash
# Check error message carefully
terraform apply

# Common fixes:
# 1. Check AWS credentials
aws sts get-caller-identity

# 2. Check service limits
aws service-quotas list-service-quotas --service-code eks

# 3. Validate configuration
terraform validate

# 4. Re-initialize
rm -rf .terraform
terraform init
```

### Can't connect to cluster

```bash
# Reconfigure kubectl
aws eks update-kubeconfig --name elevaite-staging --region us-west-1

# Verify cluster exists
aws eks describe-cluster --name elevaite-staging --region us-west-1

# Check IAM permissions
aws eks list-clusters --region us-west-1
```

### Pods not starting

```bash
# Check pod status
kubectl get pods -A

# Describe failing pod
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>

# Check node resources
kubectl top nodes
kubectl describe nodes
```

---

## ✅ Ready to Deploy?

If you checked all boxes above, you're ready!

**Next step:** Follow the [AWS Deployment Guide](./AWS_DEPLOYMENT_GUIDE.md)

```bash
cd terraform/bootstrap/aws
terraform init && terraform apply
```
