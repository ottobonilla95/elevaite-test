# =============================================================================
# ElevAIte - Development Environment (Azure)
# Shared infrastructure for PR environments (database-per-PR pattern)
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
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
# Data Sources
# =============================================================================
data "azurerm_subscription" "current" {}

data "azurerm_client_config" "current" {}

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
  source = "../../../modules/azure/database"

  environment = var.environment
  name        = var.project

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location

  database_name = "elevaite_dev"
  sku_name      = "B_Standard_B1ms" # Burstable, cheapest
  storage_mb    = 32768             # 32GB
  username      = "elevaite"
  password      = var.db_password

  backup_retention_days = 7
  high_availability     = false

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Object Storage Module (Shared for all PR environments)
# =============================================================================
module "storage" {
  source = "../../../modules/azure/storage"

  environment = var.environment
  name        = var.project

  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Kubernetes Module (Shared for all PR environments)
# =============================================================================
module "kubernetes" {
  source = "../../../modules/azure/kubernetes"

  environment  = var.environment
  name         = var.project
  cluster_name = "${var.project}-${var.environment}"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location

  kubernetes_version = "1.31"
  node_count         = 2
  min_nodes          = 1
  max_nodes          = 4
  vm_size            = "Standard_B2s" # Burstable, cheapest

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# DNS Module (Wildcard for PR environments)
# =============================================================================
module "dns" {
  source = "../../../modules/azure/dns"

  environment = var.environment
  name        = var.project

  resource_group_name = azurerm_resource_group.main.name
  domain_name         = "dev.elevaite.io"

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# Kubernetes & Helm Providers
# =============================================================================
provider "kubernetes" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  client_certificate     = base64decode(module.kubernetes.client_certificate)
  client_key             = base64decode(module.kubernetes.client_key)
}

provider "helm" {
  kubernetes {
    host                   = module.kubernetes.cluster_endpoint
    cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
    client_certificate     = base64decode(module.kubernetes.client_certificate)
    client_key             = base64decode(module.kubernetes.client_key)
  }
}

provider "kubectl" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  client_certificate     = base64decode(module.kubernetes.client_certificate)
  client_key             = base64decode(module.kubernetes.client_key)
  load_config_file       = false
}

# =============================================================================
# Cluster Add-ons
# =============================================================================
module "cluster_addons" {
  source = "../../../modules/azure/cluster-addons"

  depends_on = [module.kubernetes]

  environment            = var.environment
  domain_name            = "dev.elevaite.io"
  dns_zone_name          = module.dns.zone_name
  letsencrypt_email      = var.letsencrypt_email
  rabbitmq_password      = var.rabbitmq_password
  rabbitmq_erlang_cookie = var.rabbitmq_erlang_cookie != "" ? var.rabbitmq_erlang_cookie : random_password.rabbitmq_cookie.result
  qdrant_api_key         = var.qdrant_api_key

  resource_group_name = azurerm_resource_group.main.name
  subscription_id     = data.azurerm_subscription.current.subscription_id
  tenant_id           = data.azurerm_client_config.current.tenant_id
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
  description = "PostgreSQL hostname (shared for all PRs)"
  value       = module.database.host
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
