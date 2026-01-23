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
  
  # PostgreSQL Settings (Production - Higher specs)
  database_name      = "elevaite_production"
  instance_class     = "GP_Gen5_4"  # 4 vCores, General Purpose
  storage_mb         = 102400       # 100GB
  backup_retention   = 35           # 35 days for production
  
  # High availability
  high_availability           = true
  geo_redundant_backup        = true
  auto_grow_enabled           = true
  
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
  
  # Storage Settings (Production - GRS for redundancy)
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant for production
  
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
  
  # CloudAMQP Settings (Production - Dedicated)
  plan   = "tiger"  # Dedicated instance for production
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
  
  # AKS Settings (Production)
  kubernetes_version = "1.28"
  
  node_pools = {
    system = {
      name       = "system"
      node_count = 3
      vm_size    = "Standard_D4s_v3"
      min_count  = 3
      max_count  = 5
      mode       = "System"
    }
    application = {
      name       = "application"
      node_count = 3
      vm_size    = "Standard_D4s_v3"
      min_count  = 3
      max_count  = 10
      mode       = "User"
    }
  }
  
  # Production features
  sku_tier         = "Standard"  # Uptime SLA
  azure_policy     = true
  private_cluster  = false
  
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
