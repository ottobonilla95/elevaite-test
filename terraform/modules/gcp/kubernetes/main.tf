# =============================================================================
# Kubernetes Cluster Module (Google GKE)
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
  description = "Cluster name prefix"
  type        = string
  default     = "elevaite"
}

variable "cluster_name" {
  description = "Full cluster name (overrides name-environment pattern)"
  type        = string
  default     = ""
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "node_count" {
  description = "Initial number of nodes per zone"
  type        = number
  default     = 1
}

variable "min_nodes" {
  description = "Minimum nodes per zone for autoscaling"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum nodes per zone for autoscaling"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for nodes"
  type        = string
  default     = "e2-medium"
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "Subnetwork name"
  type        = string
  default     = "default"
}

variable "regional" {
  description = "Create regional cluster (true) or zonal (false)"
  type        = bool
  default     = true
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
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.name}-${var.environment}"
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "google_container_cluster" "main" {
  name     = local.cluster_name
  project  = var.project_id
  location = var.region

  min_master_version = var.kubernetes_version

  # We can't create a cluster with no node pool, but we want to manage them separately
  # So we create the smallest possible default pool and immediately delete it
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network
  subnetwork = var.subnetwork

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = var.environment == "production"
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  resource_labels = merge(
    {
      environment = var.environment
    },
    var.labels
  )
}

resource "google_container_node_pool" "main" {
  name     = "${local.cluster_name}-pool"
  project  = var.project_id
  location = var.region
  cluster  = google_container_cluster.main.name

  initial_node_count = var.node_count

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  node_config {
    machine_type = var.machine_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(
      {
        environment = var.environment
      },
      var.labels
    )

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.main.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = "https://${google_container_cluster.main.endpoint}"
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate (base64 encoded)"
  value       = google_container_cluster.main.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${var.region} --project ${var.project_id}"
}

output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.main.id
}

output "workload_identity_pool" {
  description = "Workload identity pool"
  value       = "${var.project_id}.svc.id.goog"
}

output "node_pool_name" {
  description = "Node pool name"
  value       = google_container_node_pool.main.name
}
