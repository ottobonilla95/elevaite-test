# =============================================================================
# ElevAIte - Development Environment (Azure)
# Shared infrastructure for PR environments (database-per-PR pattern)
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
    key                  = "dev/terraform.tfstate"
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
  default = "dev"
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
# Database Module (Shared - PR databases created dynamically)
# =============================================================================
module "database" {
  source = "../../../modules/database"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # PostgreSQL Settings (Dev - Minimum instance)
  database_name      = "elevaite_dev"  # Admin database
  instance_class     = "B_Gen5_1"      # 1 vCore, Basic tier
  storage_mb         = 20480           # 20GB
  backup_retention   = 7
  
  # No HA for dev (cost savings)
  high_availability = false
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Object Storage Module (Shared for all PR environments)
# =============================================================================
module "storage" {
  source = "../../../modules/storage"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # Storage Settings (Dev - LRS for cost savings)
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# RabbitMQ Module (Shared - vhosts per PR)
# =============================================================================
module "rabbitmq" {
  source = "../../../modules/rabbitmq"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # CloudAMQP Settings (Dev - Shared)
  plan   = "lemur"  # Free shared tier
  region = "azure-arm::eastus"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# =============================================================================
# Kubernetes Module (Shared for all PR environments)
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
  
  # AKS Settings (Dev - Smaller)
  kubernetes_version = "1.28"
  
  node_pools = {
    default = {
      name       = "default"
      node_count = 2
      vm_size    = "Standard_B2s"  # Burstable, cheapest
      min_count  = 1
      max_count  = 4
    }
  }
  
  # Dev-only - free tier
  sku_tier = "Free"
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# DNS Module (Wildcard for PR environments)
# =============================================================================
module "dns" {
  source = "../../../modules/dns"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  
  # DNS Settings (Wildcard for PRs: *.dev.elevaite.io)
  domain_name = "dev.elevaite.io"
  
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
  letsencrypt_server   = "https://acme-staging-v02.api.letsencrypt.org/directory"  # Staging for dev
  external_dns_enabled = true
  dns_zone_name        = module.dns.zone_name
}

# =============================================================================
# Monitoring Module (Dev - Minimal)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"
  
  depends_on = [module.kubernetes]
  
  environment  = var.environment
  project_name = var.project
  
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
  description = "PostgreSQL hostname (shared for all PRs)"
  value       = module.database.host
  sensitive   = true
}

output "rabbitmq_host" {
  description = "RabbitMQ hostname (shared for all PRs)"
  value       = module.rabbitmq.host
  sensitive   = true
}

output "storage_bucket" {
  description = "Storage container name (shared for all PRs)"
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
