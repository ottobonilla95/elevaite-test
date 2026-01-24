# =============================================================================
# Object Storage Module (Google Cloud Storage)
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
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

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "location" {
  description = "GCS bucket location"
  type        = string
  default     = "US"
}

variable "bucket_name" {
  description = "Bucket name (must be globally unique)"
  type        = string
  default     = ""
}

variable "storage_class" {
  description = "Storage class"
  type        = string
  default     = "STANDARD"
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

variable "labels" {
  description = "Labels for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  bucket_name = var.bucket_name != "" ? var.bucket_name : "${var.name}-${var.environment}-${var.project_id}"
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "google_storage_bucket" "main" {
  name          = local.bucket_name
  project       = var.project_id
  location      = var.location
  storage_class = var.storage_class

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

  labels = merge(
    {
      name        = replace(local.bucket_name, "-", "_")
      environment = var.environment
    },
    { for k, v in var.labels : k => replace(lower(v), "/[^a-z0-9_-]/", "_") }
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "bucket_name" {
  description = "GCS bucket name"
  value       = google_storage_bucket.main.name
}

output "bucket_url" {
  description = "GCS bucket URL"
  value       = google_storage_bucket.main.url
}

output "bucket_self_link" {
  description = "GCS bucket self link"
  value       = google_storage_bucket.main.self_link
}

output "endpoint" {
  description = "GCS endpoint URL"
  value       = "https://storage.googleapis.com"
}

output "region" {
  description = "GCS bucket location"
  value       = google_storage_bucket.main.location
}
