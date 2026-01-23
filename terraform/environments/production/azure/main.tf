# =============================================================================
# ElevAIte - Production Environment (Azure)
# =============================================================================

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "elevaite-terraform"
    storage_account_name = "elevaiteterraform"
    container_name       = "tfstate"
    key                  = "production/terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# =============================================================================
# Variables
# =============================================================================
variable "location" {
  default = "eastus"
}

variable "environment" {
  default = "production"
}

variable "project" {
  default = "elevaite"
}

# =============================================================================
# Resource Group
# =============================================================================
resource "azurerm_resource_group" "main" {
  name     = "${var.project}-${var.environment}"
  location = var.location
  
  tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# =============================================================================
# Database Module (Azure Database for PostgreSQL - Production Grade)
# =============================================================================
module "database" {
  source = "../../../modules/database"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # PostgreSQL Settings (Minimum for cost savings)
  database_name      = "elevaite_production"
  instance_class     = "B_Gen5_1"   # 1 vCore, Basic tier
  storage_mb         = 20480        # 20GB
  backup_retention   = 7

  # No HA for cost savings
  high_availability           = false
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Object Storage Module (Azure Blob Storage - Production)
# =============================================================================
module "storage" {
  source = "../../../modules/storage"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # Storage Settings (Minimum for cost savings)
  account_tier             = "Standard"
  account_replication_type = "LRS"  # Locally redundant
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# RabbitMQ Module (CloudAMQP - Production Plan)
# =============================================================================
module "rabbitmq" {
  source = "../../../modules/rabbitmq"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # CloudAMQP Settings (Minimum for cost savings)
  plan   = "lemur"  # Free tier
  region = "azure-arm::eastus"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# =============================================================================
# Kubernetes Module (Azure AKS - Production Grade)
# =============================================================================
module "kubernetes" {
  source = "../../../modules/kubernetes"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  cluster_name   = "${var.project}-${var.environment}"
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # AKS Settings (Minimum for cost savings)
  kubernetes_version = "1.28"

  node_pools = {
    default = {
      name       = "default"
      node_count = 2
      vm_size    = "Standard_B2s"  # Burstable, cheapest
      min_count  = 2
      max_count  = 3
    }
  }
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# DNS Module (Azure DNS)
# =============================================================================
module "dns" {
  source = "../../../modules/dns"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  
  # DNS Settings
  domain_name = "elevaite.io"
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Cluster Add-ons
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/cluster-addons"
  
  depends_on = [module.kubernetes]
  
  cloud_provider = "azure"
  environment    = var.environment
  
  ingress_enabled      = true
  cert_manager_enabled = true
  letsencrypt_email    = "devops@elevaite.io"
  letsencrypt_server   = "https://acme-v02.api.letsencrypt.org/directory"  # Production
  external_dns_enabled = true
  dns_zone_name        = module.dns.zone_name
}

# =============================================================================
# Monitoring Module (Production - Extended Retention)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"
  
  depends_on = [module.kubernetes]
  
  environment  = var.environment
  project_name = var.project
  
  # Prometheus settings (Production - Extended retention)
  prometheus_retention_days = 90
  prometheus_storage_size   = "100Gi"
  
  # Grafana settings
  grafana_admin_password = var.grafana_password
  grafana_domain         = "grafana.elevaite.io"
  
  # Loki settings (Production - Extended retention)
  loki_retention_days  = 30
  loki_storage_size    = "50Gi"
  
  # Alerting (Production - Full alerting)
  alertmanager_enabled      = true
  slack_webhook_url         = var.slack_webhook_url
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
  description = "PostgreSQL hostname"
  value       = module.database.host
  sensitive   = true
}

output "rabbitmq_host" {
  description = "RabbitMQ hostname"
  value       = module.rabbitmq.host
  sensitive   = true
}

output "storage_bucket" {
  description = "Storage container name"
  value       = module.storage.bucket_name
}

output "kubernetes_cluster_name" {
  description = "AKS cluster name"
  value       = module.kubernetes.cluster_name
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.kubernetes.cluster_name}"
}

output "monitoring_grafana_url" {
  description = "Grafana dashboard URL"
  value       = "https://grafana.elevaite.io"
}
