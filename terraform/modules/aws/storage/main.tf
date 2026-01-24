# =============================================================================
# Object Storage Module (AWS S3)
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "elevaite"
}

variable "bucket_name" {
  description = "Bucket name (must be globally unique)"
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

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  bucket_name = var.bucket_name != "" ? var.bucket_name : "${var.name}-${var.environment}"
}

# =============================================================================
# RESOURCES
# =============================================================================

data "aws_region" "current" {}

resource "aws_s3_bucket" "main" {
  bucket = local.bucket_name

  tags = merge(
    {
      Name        = local.bucket_name
      Environment = var.environment
    },
    var.tags
  )
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count = var.environment == "production" ? 1 : 0

  bucket = aws_s3_bucket.main.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    filter {}

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
# OUTPUTS
# =============================================================================

output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "endpoint" {
  description = "S3 endpoint URL"
  value       = "https://s3.${data.aws_region.current.name}.amazonaws.com"
}

output "region" {
  description = "S3 bucket region"
  value       = data.aws_region.current.name
}
