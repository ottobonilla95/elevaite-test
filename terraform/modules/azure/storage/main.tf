# =============================================================================
# Object Storage Module (Azure Blob Storage)
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
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
  description = "Name prefix for resources"
  type        = string
  default     = "elevaite"
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

variable "container_name" {
  description = "Blob container name"
  type        = string
  default     = ""
}

variable "enable_versioning" {
  description = "Enable blob versioning"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  # Azure storage account names must be lowercase, alphanumeric, 3-24 chars
  storage_account_name = replace(lower("${var.name}${var.environment}"), "-", "")
  container_name       = var.container_name != "" ? var.container_name : "${var.name}-${var.environment}"
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "azurerm_storage_account" "main" {
  name                     = substr(local.storage_account_name, 0, 24)
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.environment == "production" ? "GRS" : var.account_replication_type

  min_tls_version = "TLS1_2"

  blob_properties {
    versioning_enabled = var.enable_versioning
  }

  tags = merge(
    {
      Name        = "${var.name}-${var.environment}"
      Environment = var.environment
    },
    var.tags
  )
}

resource "azurerm_storage_container" "main" {
  name                  = local.container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "bucket_name" {
  description = "Storage container name"
  value       = azurerm_storage_container.main.name
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_id" {
  description = "Storage account ID"
  value       = azurerm_storage_account.main.id
}

output "endpoint" {
  description = "Primary blob endpoint"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "connection_string" {
  description = "Primary connection string"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}
