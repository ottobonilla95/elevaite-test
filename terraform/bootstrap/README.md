# Terraform Bootstrap

This directory contains the **bootstrap configuration** to set up Terraform's remote state backend.

## Why Bootstrap?

Terraform needs a place to store its state file (who owns what resources). We use:
- **S3/GCS/Azure Blob** for state storage
- **DynamoDB/Firestore/Azure Table** for state locking (prevents concurrent runs)

## First-Time Setup

Run this **once per cloud provider** before using other Terraform configs:

### AWS
```bash
cd aws
terraform init
terraform apply
```

### Azure
```bash
cd azure
terraform init
terraform apply
```

### GCP
```bash
cd gcp
terraform init
terraform apply
```

## After Bootstrap

The bootstrap creates the backend resources. Then update your environment configs to use them:

```hcl
# terraform/environments/staging/aws/main.tf
terraform {
  backend "s3" {
    bucket         = "elevaite-terraform-state"
    key            = "staging/aws/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "elevaite-terraform-locks"
  }
}
```

## Important

The bootstrap itself uses **local state** (stored in this directory). Keep this directory secure or migrate its state to the newly created backend after first run.
