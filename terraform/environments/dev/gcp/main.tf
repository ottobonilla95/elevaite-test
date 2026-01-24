# =============================================================================
# ElevAIte - Development Environment (Google Cloud Platform)
# Shared infrastructure for PR environments (database-per-PR pattern)
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "gcs" {
    bucket = "elevaite-terraform-state"
    prefix = "dev/terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# Variables
# =============================================================================
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  default = "us-central1"
}

variable "environment" {
  default = "dev"
}

variable "project_name" {
  default = "elevaite"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "grafana_password" {
  type      = string
  sensitive = true
}

variable "letsencrypt_email" {
  type    = string
  default = "devops@elevaite.io"
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

variable "rabbitmq_erlang_cookie" {
  description = "RabbitMQ Erlang cookie for cluster communication"
  type        = string
  sensitive   = true
  default     = ""
}

variable "qdrant_api_key" {
  description = "Qdrant API key for authentication"
  type        = string
  sensitive   = true
}

# =============================================================================
# Database Module (Shared - PR databases created dynamically)
# =============================================================================
module "database" {
  source = "../../../modules/gcp/database"

  environment = var.environment
  name        = var.project_name

  project_id = var.project_id
  region     = var.region

  database_name = "elevaite_dev"
  tier          = "db-f1-micro" # Smallest instance
  disk_size     = 20
  username      = "elevaite"
  password      = var.db_password

  backup_retention_days = 7
  high_availability     = false

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }
}

# =============================================================================
# Object Storage Module (Shared for all PR environments)
# =============================================================================
module "storage" {
  source = "../../../modules/gcp/storage"

  environment = var.environment
  name        = var.project_name

  project_id    = var.project_id
  location      = var.region
  storage_class = "STANDARD"

  enable_versioning = false # Not needed for dev
  lifecycle_days    = 30

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Kubernetes Module (Shared for all PR environments)
# =============================================================================
module "kubernetes" {
  source = "../../../modules/gcp/kubernetes"

  environment  = var.environment
  name         = var.project_name
  cluster_name = "${var.project_name}-${var.environment}"

  project_id = var.project_id
  region     = var.region

  kubernetes_version = "1.31"
  node_count         = 1
  min_nodes          = 1
  max_nodes          = 4
  machine_type       = "e2-medium" # More memory (4GB vs 2GB)

  network    = "default"
  subnetwork = "default"

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# DNS Module (Wildcard for PR environments)
# =============================================================================
module "dns" {
  source = "../../../modules/gcp/dns"

  environment = var.environment
  name        = var.project_name

  project_id  = var.project_id
  domain_name = "dev.elevaite.io"

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Kubernetes & Helm Providers
# =============================================================================
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  token                  = data.google_client_config.default.access_token
}

provider "helm" {
  kubernetes {
    host                   = module.kubernetes.cluster_endpoint
    cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
    token                  = data.google_client_config.default.access_token
  }
}

provider "kubectl" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  token                  = data.google_client_config.default.access_token
  load_config_file       = false
}

# =============================================================================
# Cluster Add-ons
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/gcp/cluster-addons"

  depends_on = [module.kubernetes]

  environment            = var.environment
  domain_name            = "dev.elevaite.io"
  dns_zone_name          = module.dns.zone_name
  letsencrypt_email      = var.letsencrypt_email
  rabbitmq_password      = var.rabbitmq_password
  rabbitmq_erlang_cookie = var.rabbitmq_erlang_cookie != "" ? var.rabbitmq_erlang_cookie : random_password.rabbitmq_cookie.result
  qdrant_api_key         = var.qdrant_api_key

  project_id             = var.project_id
  workload_identity_pool = module.kubernetes.workload_identity_pool
}

resource "random_password" "rabbitmq_cookie" {
  length  = 32
  special = false
}

# =============================================================================
# Monitoring Module (Dev - Minimal)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"

  depends_on = [module.cluster_addons]

  environment = var.environment
  domain_name = "dev.elevaite.io"

  grafana_admin_password = var.grafana_password
  retention_days         = 3
}

# =============================================================================
# Outputs
# =============================================================================
output "database_host" {
  description = "Cloud SQL host (shared for all PRs)"
  value       = module.database.host
  sensitive   = true
}

output "storage_bucket" {
  description = "GCS bucket name (shared for all PRs)"
  value       = module.storage.bucket_name
}

output "kubernetes_cluster_name" {
  description = "GKE cluster name"
  value       = module.kubernetes.cluster_name
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = module.kubernetes.kubeconfig_command
}

output "qdrant_host" {
  value = module.cluster_addons.qdrant_host
}

output "rabbitmq_host" {
  value = module.cluster_addons.rabbitmq_host
}

output "helm_values" {
  description = "Values to pass to Helm for PR deployments"
  value = {
    postgresql_host = module.database.host
    storage_bucket  = module.storage.bucket_name
    qdrant_host     = module.cluster_addons.qdrant_host
    rabbitmq_host   = module.cluster_addons.rabbitmq_host
  }
}
