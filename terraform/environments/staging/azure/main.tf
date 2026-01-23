# =============================================================================
# ElevAIte - Staging Environment (Azure)
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
    key                  = "staging/terraform.tfstate"
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
  default = "staging"
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
# Database Module (Azure Database for PostgreSQL)
# =============================================================================
module "database" {
  source = "../../../modules/database"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # PostgreSQL Settings
  database_name      = "elevaite_staging"
  instance_class     = "GP_Gen5_2"  # 2 vCores, General Purpose
  storage_mb         = 51200        # 50GB
  backup_retention   = 14
  
  # High availability
  high_availability = true
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Object Storage Module (Azure Blob Storage)
# =============================================================================
module "storage" {
  source = "../../../modules/storage"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # Azure-specific
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  
  # Storage Settings
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# RabbitMQ Module (CloudAMQP - Cloud-Agnostic)
# =============================================================================
module "rabbitmq" {
  source = "../../../modules/rabbitmq"
  
  cloud_provider = "azure"
  environment    = var.environment
  project_name   = var.project
  
  # CloudAMQP Settings
  plan     = "lemur"  # Shared instance
  region   = "azure-arm::eastus"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# =============================================================================
# Kubernetes Module (Azure AKS)
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
  
  # AKS Settings
  kubernetes_version = "1.28"
  
  node_pools = {
    default = {
      name       = "default"
      node_count = 2
      vm_size    = "Standard_D2s_v3"
      min_count  = 2
      max_count  = 4
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
  domain_name = "staging.elevaite.io"
  
  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Cluster Add-ons (Ingress, Cert-Manager, External-DNS)
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/cluster-addons"
  
  depends_on = [module.kubernetes]
  
  cloud_provider = "azure"
  environment    = var.environment
  
  # Ingress settings
  ingress_enabled = true
  
  # SSL settings
  cert_manager_enabled = true
  letsencrypt_email    = "devops@elevaite.io"
  
  # External DNS settings
  external_dns_enabled = true
  dns_zone_name        = module.dns.zone_name
}

# =============================================================================
# Monitoring Module (Prometheus, Grafana, Loki)
# =============================================================================
module "monitoring" {
  source = "../../../modules/monitoring"
  
  depends_on = [module.kubernetes]
  
  environment  = var.environment
  project_name = var.project
  
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
  value       = "https://grafana-staging.elevaite.io"
}
