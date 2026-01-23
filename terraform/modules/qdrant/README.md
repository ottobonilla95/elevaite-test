# Qdrant Terraform Module

This module provisions a managed Qdrant vector database cluster via Qdrant Cloud.

## Overview

Qdrant Cloud is a fully managed vector database service. This module provides Terraform configuration for provisioning Qdrant clusters.

## Current Implementation Status

The Qdrant Terraform provider is still in early development. This module provides:

1. **Template configuration** for when the provider is stable
2. **Output structure** for manual cluster integration
3. **Documentation** for manual cluster creation

## Manual Cluster Creation (Current Approach)

### Step 1: Create Cluster in Qdrant Cloud Console

1. Go to [Qdrant Cloud Console](https://cloud.qdrant.io/)
2. Create a new cluster:
   - **Name**: `elevaite-{environment}` (e.g., `elevaite-production`)
   - **Cloud Provider**: AWS / GCP / Azure
   - **Region**: Match your Kubernetes cluster region
   - **Configuration**:
     - Dev: `1x-small` (1 node, free tier)
     - Staging: `1x-medium` (1 node)
     - Production: `3x-large` (3 nodes, HA)
   - **Storage**: 10GB (dev), 50GB+ (production)

3. Save the cluster URL and API key

### Step 2: Configure Terraform Variables

Create a `terraform.tfvars` file in your environment:

```hcl
# Dev example
qdrant_cluster_url = "https://elevaite-dev.qdrant.io:6334"

# Staging example
qdrant_cluster_url = "https://elevaite-staging.qdrant.io:6334"

# Production example
qdrant_cluster_url = "https://elevaite-production.qdrant.io:6334"
```

### Step 3: Store API Key in Secrets Manager

**AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name qdrant-api-key-production \
  --secret-string '{"api_key":"your-qdrant-api-key"}'
```

**Azure Key Vault:**
```bash
az keyvault secret set \
  --vault-name elevaite-production \
  --name qdrant-api-key \
  --value "your-qdrant-api-key"
```

**GCP Secret Manager:**
```bash
echo -n "your-qdrant-api-key" | \
  gcloud secrets create qdrant-api-key-production \
  --data-file=-
```

### Step 4: Configure Helm Chart

The Helm chart will inject the Qdrant URL and API key:

```yaml
# helm/elevaite/values-production.yaml
qdrant:
  enabled: true
  host: elevaite-production.qdrant.io
  port: 6333
  apiKeySecret:
    name: qdrant-api-key-production
    key: api_key
```

## Future: Automated Provisioning

When the Qdrant Terraform provider is stable, uncomment the resource in `main.tf`:

```hcl
resource "qdrant_cluster" "main" {
  name               = local.cluster_name
  cloud_provider     = local.qdrant_cloud_provider
  cloud_region       = var.region
  node_configuration = var.node_configuration
  cluster_size       = var.cluster_size
}
```

## Module Usage

```hcl
module "qdrant" {
  source = "../../../modules/qdrant"

  environment    = "production"
  project_name   = "elevaite"
  cloud_provider = "aws"
  region         = "us-west-1"

  # Production settings
  cluster_size       = 3
  node_configuration = "1x-large"
  storage_size_gb    = 100

  # Manual cluster URL (until provider is stable)
  qdrant_cluster_url = "https://elevaite-production.qdrant.io:6334"
}
```

## Outputs

- `cluster_url`: gRPC endpoint (port 6334)
- `cluster_rest_url`: REST API endpoint (port 6333)
- `cluster_name`: Cluster identifier
- `api_key_secret_name`: Expected secret name in secrets manager

## Cost Optimization

### Development
- Use free tier: `1x-small` (1 node, 1GB RAM, 10GB storage)
- Cost: **$0/month**

### Staging
- Use `1x-medium` (1 node, 4GB RAM, 25GB storage)
- Cost: **~$50/month**

### Production
- Use `3x-large` (3 nodes, 16GB RAM each, 100GB storage each)
- High availability with automatic failover
- Cost: **~$500/month**

## Networking

Qdrant Cloud clusters are publicly accessible with:
- TLS encryption
- API key authentication
- IP allowlist (optional)

For enhanced security, consider:
1. VPC peering (AWS/GCP)
2. Private Link (AWS)
3. Private Service Connect (GCP)

## Migration from Self-Hosted

If migrating from Docker Compose Qdrant:

1. Create snapshot of local Qdrant data
2. Upload to Qdrant Cloud cluster via API
3. Update application connection strings
4. Verify data integrity
5. Switch traffic to cloud cluster

## Monitoring

Qdrant Cloud provides:
- Built-in metrics dashboard
- Query performance analytics
- Storage usage tracking
- Automatic alerts

Export metrics to your monitoring stack:
```yaml
# Prometheus integration
- job_name: 'qdrant'
  static_configs:
    - targets: ['elevaite-production.qdrant.io:6333']
  metrics_path: '/metrics'
  bearer_token: '${QDRANT_API_KEY}'
```

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
curl https://elevaite-production.qdrant.io:6333/collections \
  -H "api-key: your-api-key"
```

### Performance Issues
- Check node configuration (upgrade if needed)
- Review query patterns (add indexes)
- Monitor memory usage
- Consider increasing cluster size

## References

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [Qdrant Terraform Provider](https://registry.terraform.io/providers/qdrant/qdrant)
- [Pricing Calculator](https://qdrant.tech/pricing/)
