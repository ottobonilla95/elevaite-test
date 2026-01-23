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

# =============================================================================
# Database Module (Shared - PR databases created dynamically)
# =============================================================================
module "database" {
  source = "../../../modules/database"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  region         = var.region
  
  # PostgreSQL Settings (Dev - Smaller instance)
  database_name     = "elevaite_dev"  # Admin database
  database_version  = "POSTGRES_15"
  instance_class    = "db-f1-micro"   # Smallest instance
  disk_size_gb      = 20
  disk_autoresize   = true
  backup_retention  = 7
  
  # No HA for dev
  high_availability = false
  
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
  source = "../../../modules/storage"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  location       = var.region
  
  # Storage Settings (Dev - Standard)
  storage_class      = "STANDARD"
  versioning         = false
  lifecycle_age_days = 30
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# RabbitMQ Module (Shared - vhosts per PR)
# =============================================================================
module "rabbitmq" {
  source = "../../../modules/rabbitmq"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # CloudAMQP Settings (Dev - Free)
  plan   = "lemur"  # Free tier
  region = "google-compute-engine::us-central1"
  
  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Kubernetes Module (Shared for all PR environments)
# =============================================================================
module "kubernetes" {
  source = "../../../modules/kubernetes"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  cluster_name   = "${var.project_name}-${var.environment}"
  
  # GCP-specific
  gcp_project_id = var.project_id
  region         = var.region
  
  # GKE Settings (Dev - Smaller, Zonal)
  kubernetes_version = "1.28"
  regional           = false  # Zonal for cost savings
  
  node_pools = {
    default = {
      name           = "default-pool"
      node_count     = 2
      machine_type   = "e2-micro"  # Smallest instance
      min_node_count = 1
      max_node_count = 4
      disk_size_gb   = 30
      disk_type      = "pd-standard"
      preemptible    = true  # Spot instances for dev
    }
  }
  
  # Network settings
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
  source = "../../../modules/dns"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  
  # DNS Settings (Wildcard for PRs: *.dev.elevaite.io)
  domain_name = "dev.elevaite.io"
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Cluster Add-ons
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/cluster-addons"
  
  depends_on = [module.kubernetes]
  
  cloud_provider = "gcp"
  environment    = var.environment
  
  ingress_enabled      = true
  cert_manager_enabled = true
  letsencrypt_email    = "devops@elevaite.io"
  letsencrypt_server   = "https://acme-staging-v02.api.letsencrypt.org/directory"  # Staging for dev
  external_dns_enabled = true
  dns_zone_name        = module.dns.zone_name
  gcp_project_id       = var.project_id
}

# =============================================================================
# Monitoring Module (Dev - Minimal)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"
  
  depends_on = [module.kubernetes]
  
  environment  = var.environment
  project_name = var.project_name
  
  # Prometheus settings (Dev - Short retention)
  prometheus_retention_days = 3
  prometheus_storage_size   = "10Gi"
  
  # Grafana settings
  grafana_admin_password = var.grafana_password
  grafana_domain         = "grafana-dev.elevaite.io"
  
  # Loki settings (Dev - Short retention)
  loki_retention_days  = 3
  loki_storage_size    = "5Gi"
  
  # No alerting for dev
  alertmanager_enabled = false
}

variable "grafana_password" {
  type      = string
  sensitive = true
}

# =============================================================================
# Outputs
# =============================================================================
output "database_host" {
  description = "Cloud SQL host (shared for all PRs)"
  value       = module.database.host
  sensitive   = true
}

output "rabbitmq_host" {
  description = "RabbitMQ hostname (shared for all PRs)"
  value       = module.rabbitmq.host
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
  value       = "gcloud container clusters get-credentials ${module.kubernetes.cluster_name} --region ${var.region} --project ${var.project_id}"
}
