# =============================================================================
# PostgreSQL Database Module (Azure Database for PostgreSQL)
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

variable "sku_name" {
  description = "SKU name for the PostgreSQL server"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "storage_mb" {
  description = "Storage size in MB"
  type        = number
  default     = 32768
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "elevaite"
}

variable "username" {
  description = "Administrator username"
  type        = string
  default     = "elevaite"
}

variable "password" {
  description = "Administrator password"
  type        = string
  sensitive   = true
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "high_availability" {
  description = "Enable high availability (zone redundant)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "${var.name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  version = var.postgres_version

  sku_name = var.environment == "production" ? "GP_Standard_D2s_v3" : var.sku_name

  storage_mb = var.storage_mb

  administrator_login    = var.username
  administrator_password = var.password

  backup_retention_days = var.backup_retention_days

  geo_redundant_backup_enabled = var.environment == "production"

  zone = var.high_availability ? "1" : null

  tags = merge(
    {
      Name        = "${var.name}-${var.environment}"
      Environment = var.environment
    },
    var.tags
  )
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "host" {
  description = "Database host (FQDN)"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "port" {
  description = "Database port"
  value       = 5432
}

output "database_name" {
  description = "Database name"
  value       = var.database_name
}

output "username" {
  description = "Database username"
  value       = var.username
}

output "server_id" {
  description = "PostgreSQL server ID"
  value       = azurerm_postgresql_flexible_server.main.id
}

output "connection_string" {
  description = "Full connection string (without password)"
  value       = "postgresql://${var.username}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.database_name}?sslmode=require"
}
