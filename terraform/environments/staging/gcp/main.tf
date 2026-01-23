# =============================================================================
# ElevAIte - Staging Environment (Google Cloud Platform)
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
    prefix = "staging/terraform.tfstate"
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
  default = "staging"
}

variable "project_name" {
  default = "elevaite"
}

# =============================================================================
# Database Module (Cloud SQL for PostgreSQL)
# =============================================================================
module "database" {
  source = "../../../modules/database"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  region         = var.region
  
  # PostgreSQL Settings (Minimum for cost savings)
  database_name     = "elevaite_staging"
  database_version  = "POSTGRES_15"
  instance_class    = "db-f1-micro"  # Smallest instance
  disk_size_gb      = 20
  backup_retention  = 7

  # No HA for cost savings
  high_availability = false
  
  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }
}

# =============================================================================
# Object Storage Module (Google Cloud Storage)
# =============================================================================
module "storage" {
  source = "../../../modules/storage"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  location       = var.region
  
  # Storage Settings
  storage_class     = "STANDARD"
  versioning        = true
  lifecycle_age_days = 90
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Kubernetes Module (Google Kubernetes Engine)
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
  
  # GKE Settings
  kubernetes_version = "1.28"
  
  node_pools = {
    default = {
      name           = "default-pool"
      node_count     = 2
      machine_type   = "e2-micro"  # Smallest instance
      min_node_count = 2
      max_node_count = 3
      disk_size_gb   = 30
      disk_type      = "pd-standard"
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
# DNS Module (Cloud DNS)
# =============================================================================
module "dns" {
  source = "../../../modules/dns"
  
  cloud_provider = "gcp"
  environment    = var.environment
  project_name   = var.project_name
  
  # GCP-specific
  gcp_project_id = var.project_id
  
  # DNS Settings
  domain_name = "staging.elevaite.io"
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# =============================================================================
# Cluster Add-ons (Ingress, Cert-Manager, External-DNS)
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/cluster-addons"
  
  depends_on = [module.kubernetes]
  
  cloud_provider = "gcp"
  environment    = var.environment
  
  # Ingress settings
  ingress_enabled = true
  
  # SSL settings
  cert_manager_enabled = true
  letsencrypt_email    = "devops@elevaite.io"
  
  # External DNS settings
  external_dns_enabled = true
  dns_zone_name        = module.dns.zone_name
  gcp_project_id       = var.project_id
}

# =============================================================================
# Monitoring Module (Prometheus, Grafana, Loki)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"
  
  depends_on = [module.kubernetes]
  
  environment  = var.environment
  project_name = var.project_name
  
  # Prometheus settings
  prometheus_retention_days = 15
  prometheus_storage_size   = "20Gi"
  
  # Grafana settings
  grafana_admin_password = var.grafana_password
  grafana_domain         = "grafana-staging.elevaite.io"
  
  # Loki settings
  loki_retention_days  = 7
  loki_storage_size    = "10Gi"
  
  # Alerting
  alertmanager_enabled     = true
  slack_webhook_url        = var.slack_webhook_url
  pagerduty_integration_key = var.pagerduty_key
}

variable "grafana_password" {
  type      = string
  sensitive = true
}

variable "slack_webhook_url" {
  type    = string
  default = ""
}

variable "pagerduty_key" {
  type    = string
  default = ""
}

# =============================================================================
# Outputs
# =============================================================================
output "database_host" {
  description = "Cloud SQL private IP"
  value       = module.database.host
  sensitive   = true
}

output "storage_bucket" {
  description = "GCS bucket name"
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

output "monitoring_grafana_url" {
  description = "Grafana dashboard URL"
  value       = "https://grafana-staging.elevaite.io"
}
