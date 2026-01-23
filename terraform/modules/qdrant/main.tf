# =============================================================================
# Qdrant Module (Managed Qdrant Cloud)
# Provisions managed Qdrant vector database via Qdrant Cloud
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    qdrant = {
      source  = "qdrant/qdrant"
      version = "~> 1.0"
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
  description = "Cluster name prefix"
  type        = string
  default     = "elevaite"
}

# Alias for multi-cloud compatibility
variable "project_name" {
  description = "Alias for name (multi-cloud compatibility)"
  type        = string
  default     = ""
}

variable "cloud_provider" {
  description = "Cloud provider for Qdrant cluster: aws, gcp, or azure"
  type        = string
  validation {
    condition     = contains(["aws", "gcp", "azure"], var.cloud_provider)
    error_message = "cloud_provider must be one of: aws, gcp, azure"
  }
}

variable "region" {
  description = "Cloud region (e.g., us-west-1, us-central1, eastus)"
  type        = string
}

variable "cluster_size" {
  description = "Number of nodes in cluster (1 for dev, 3+ for production)"
  type        = number
  default     = 1
}

variable "node_configuration" {
  description = "Node configuration ID from Qdrant Cloud"
  type        = string
  default     = "1x-small"  # Free tier / dev
}

variable "storage_size_gb" {
  description = "Storage size in GB per node"
  type        = number
  default     = 10
}

# =============================================================================
# LOCALS - Resolve variable aliases
# =============================================================================

locals {
  # Resolve name (project_name alias)
  resolved_name = var.project_name != "" ? var.project_name : var.name

  # Map Terraform cloud provider to Qdrant Cloud provider names
  qdrant_cloud_provider = {
    aws   = "aws"
    gcp   = "gcp"
    azure = "azure"
  }[var.cloud_provider]

  # Cluster name
  cluster_name = "${local.resolved_name}-${var.environment}"
}

# =============================================================================
# QDRANT CLOUD CLUSTER
# =============================================================================

# Note: This requires the Qdrant Terraform provider to be configured with API key
# export QDRANT_CLOUD_API_KEY="your-api-key"
#
# For actual implementation, you would use:
# resource "qdrant_cluster" "main" {
#   name               = local.cluster_name
#   cloud_provider     = local.qdrant_cloud_provider
#   cloud_region       = var.region
#   node_configuration = var.node_configuration
#   cluster_size       = var.cluster_size
# }
#
# Since the Qdrant provider is still in development, we provide this as a template.
# For now, clusters should be created manually via Qdrant Cloud Console:
# https://cloud.qdrant.io/

# =============================================================================
# PLACEHOLDER OUTPUTS (Manual Cluster Creation)
# =============================================================================
# When using manual cluster creation, these values need to be:
# 1. Created in Qdrant Cloud Console
# 2. Passed to Terraform via variables or data sources
# 3. Output for use by application configuration

output "cluster_url" {
  description = "Qdrant cluster gRPC endpoint"
  value       = var.qdrant_cluster_url != "" ? var.qdrant_cluster_url : "https://${local.cluster_name}.qdrant.io:6334"
  sensitive   = false
}

output "cluster_rest_url" {
  description = "Qdrant cluster REST API endpoint"
  value       = var.qdrant_cluster_url != "" ? replace(var.qdrant_cluster_url, ":6334", ":6333") : "https://${local.cluster_name}.qdrant.io:6333"
  sensitive   = false
}

output "cluster_name" {
  description = "Qdrant cluster name"
  value       = local.cluster_name
}

# API key should be stored in secrets manager and injected into application
output "api_key_secret_name" {
  description = "Name of secret containing Qdrant API key"
  value       = "qdrant-api-key-${var.environment}"
}

# =============================================================================
# ADDITIONAL VARIABLES FOR MANUAL CLUSTER
# =============================================================================

variable "qdrant_cluster_url" {
  description = "Manually created Qdrant cluster URL (if not using Terraform provider)"
  type        = string
  default     = ""
  sensitive   = false
}

variable "qdrant_api_key" {
  description = "Qdrant Cloud API key (for cluster creation)"
  type        = string
  default     = ""
  sensitive   = true
}
