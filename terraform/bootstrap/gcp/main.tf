# =============================================================================
# Terraform Bootstrap - GCP
# Creates GCS bucket for Terraform state management
# Run this ONCE before using other Terraform configurations
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

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "elevaite"
}

# =============================================================================
# GCS BUCKET FOR STATE
# =============================================================================

resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_name}-terraform-state-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  labels = {
    project   = var.project_name
    managedby = "terraform-bootstrap"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "state_bucket_name" {
  description = "GCS bucket for Terraform state"
  value       = google_storage_bucket.terraform_state.name
}

output "backend_config" {
  description = "Backend configuration to use in other Terraform configs"
  value       = <<-EOT
    terraform {
      backend "gcs" {
        bucket = "${google_storage_bucket.terraform_state.name}"
        prefix = "ENV/gcp"  # Replace ENV with dev/staging/production
      }
    }
  EOT
}
