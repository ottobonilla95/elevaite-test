# =============================================================================
# Object Storage Module (Multi-Cloud)
# Provisions managed storage: AWS S3, Azure Blob, Google Cloud Storage
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "cloud_provider" {
  description = "Cloud provider: aws, azure, or gcp"
  type        = string
}

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "elevaite"
}

# Alias for multi-cloud compatibility
variable "project_name" {
  description = "Alias for name (multi-cloud compatibility)"
  type        = string
  default     = ""
}

variable "bucket_name" {
  description = "Bucket/container name (must be globally unique)"
  type        = string
  default     = ""
}

variable "enable_versioning" {
  description = "Enable object versioning"
  type        = bool
  default     = true
}

variable "lifecycle_days" {
  description = "Days to retain objects before transitioning to cheaper storage"
  type        = number
  default     = 90
}

# Azure specific
variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = ""
}

variable "location" {
  description = "Azure/GCP region"
  type        = string
  default     = "eastus"
}

# GCP specific
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = ""
}

# Alias for multi-cloud compatibility
variable "gcp_project_id" {
  description = "Alias for project_id (GCP compatibility)"
  type        = string
  default     = ""
}

# =============================================================================
# LOCALS - Resolve variable aliases for multi-cloud compatibility
# =============================================================================

locals {
  # Resolve name (project_name alias)
  resolved_name = var.project_name != "" ? var.project_name : var.name

  # Resolve GCP project ID (gcp_project_id alias)
  resolved_project_id = var.gcp_project_id != "" ? var.gcp_project_id : var.project_id

  # Generate bucket name if not provided
  resolved_bucket_name = var.bucket_name != "" ? var.bucket_name : "${local.resolved_name}-${var.environment}"
}

# =============================================================================
# AWS S3
# =============================================================================

resource "aws_s3_bucket" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = local.resolved_bucket_name

  tags = {
    Name        = local.resolved_bucket_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.main[0].id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.main[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.main[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count = var.cloud_provider == "aws" && var.environment == "production" ? 1 : 0

  bucket = aws_s3_bucket.main[0].id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = var.lifecycle_days
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# =============================================================================
# Azure Blob Storage
# =============================================================================

resource "azurerm_storage_account" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name                     = replace("${local.resolved_name}${var.environment}", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.environment == "production" ? "Standard" : "Standard"
  account_replication_type = var.environment == "production" ? "GRS" : "LRS"

  min_tls_version = "TLS1_2"

  blob_properties {
    versioning_enabled = var.enable_versioning
  }

  tags = {
    Name        = "${local.resolved_name}-${var.environment}"
    Environment = var.environment
  }
}

resource "azurerm_storage_container" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name                  = local.resolved_bucket_name
  storage_account_name  = azurerm_storage_account.main[0].name
  container_access_type = "private"
}

# =============================================================================
# Google Cloud Storage
# =============================================================================

resource "google_storage_bucket" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name          = local.resolved_bucket_name
  project       = local.resolved_project_id
  location      = var.location
  storage_class = var.environment == "production" ? "STANDARD" : "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    name        = replace(local.resolved_bucket_name, "-", "_")
    environment = var.environment
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "bucket_name" {
  description = "Bucket/container name"
  value       = var.bucket_name
}

output "endpoint" {
  description = "Storage endpoint URL"
  value = coalesce(
    var.cloud_provider == "aws" ? "https://s3.amazonaws.com" : "",
    var.cloud_provider == "azure" ? try(azurerm_storage_account.main[0].primary_blob_endpoint, "") : "",
    var.cloud_provider == "gcp" ? "https://storage.googleapis.com" : ""
  )
}

output "region" {
  description = "Storage region"
  value = coalesce(
    var.cloud_provider == "aws" ? data.aws_region.current[0].name : "",
    var.cloud_provider == "azure" ? var.location : "",
    var.cloud_provider == "gcp" ? var.location : ""
  )
}

data "aws_region" "current" {
  count = var.cloud_provider == "aws" ? 1 : 0
}
