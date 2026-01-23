# =============================================================================
# PostgreSQL Database Module (Multi-Cloud)
# Provisions managed PostgreSQL: AWS RDS, Azure Database, Google Cloud SQL
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "cloud_provider" {
  description = "Cloud provider: aws, azure, or gcp"
  type        = string
  validation {
    condition     = contains(["aws", "azure", "gcp"], var.cloud_provider)
    error_message = "cloud_provider must be one of: aws, azure, gcp"
  }
}

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "elevaite"
}

# Alias for multi-cloud compatibility
variable "project_name" {
  description = "Alias for name (multi-cloud compatibility)"
  type        = string
  default     = ""
}

variable "instance_class" {
  description = "Instance class/size"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "Storage size in GB"
  type        = number
  default     = 20
}

# Aliases for multi-cloud compatibility
variable "storage_mb" {
  description = "Storage size in MB (Azure compatibility, converts to allocated_storage)"
  type        = number
  default     = 0
}

variable "disk_size_gb" {
  description = "Disk size in GB (GCP compatibility, alias for allocated_storage)"
  type        = number
  default     = 0
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "elevaite"
}

variable "username" {
  description = "Master username"
  type        = string
  default     = "elevaite"
}

variable "password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

# Alias for multi-cloud compatibility
variable "high_availability" {
  description = "Alias for multi_az (multi-cloud compatibility)"
  type        = bool
  default     = null
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# Networking
variable "vpc_id" {
  description = "VPC ID (AWS)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs (AWS)"
  type        = list(string)
  default     = []
}

# Azure specific
variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = ""
}

variable "location" {
  description = "Azure/GCP region"
  type        = string
  default     = "eastus"
}

# Alias for multi-cloud compatibility
variable "region" {
  description = "Alias for location (multi-cloud compatibility)"
  type        = string
  default     = ""
}

# GCP specific
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = ""
}

# Alias for multi-cloud compatibility
variable "gcp_project_id" {
  description = "Alias for project_id (GCP compatibility)"
  type        = string
  default     = ""
}

variable "network_name" {
  description = "GCP VPC network name"
  type        = string
  default     = ""
}

# =============================================================================
# LOCALS - Resolve variable aliases for multi-cloud compatibility
# =============================================================================

locals {
  # Resolve name (project_name alias)
  resolved_name = var.project_name != "" ? var.project_name : var.name

  # Resolve storage size (handle multiple formats)
  resolved_storage_gb = (
    var.disk_size_gb > 0 ? var.disk_size_gb :
    var.storage_mb > 0 ? ceil(var.storage_mb / 1024) :
    var.allocated_storage
  )

  # Resolve multi-az (high_availability alias)
  resolved_multi_az = var.high_availability != null ? var.high_availability : var.multi_az

  # Resolve location (region alias)
  resolved_location = var.region != "" ? var.region : var.location

  # Resolve GCP project ID (gcp_project_id alias)
  resolved_project_id = var.gcp_project_id != "" ? var.gcp_project_id : var.project_id
}

# =============================================================================
# AWS RDS PostgreSQL
# =============================================================================

resource "aws_db_subnet_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name       = "${local.resolved_name}-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "${local.resolved_name}-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_db_instance" "postgres" {
  count = var.cloud_provider == "aws" ? 1 : 0

  identifier = "${local.resolved_name}-${var.environment}"

  engine               = "postgres"
  engine_version       = "15"
  instance_class       = var.instance_class
  allocated_storage    = local.resolved_storage_gb
  max_allocated_storage = local.resolved_storage_gb * 2

  db_name  = var.database_name
  username = var.username
  password = var.password

  multi_az               = local.resolved_multi_az
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = var.security_group_ids

  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  storage_encrypted = true
  storage_type      = "gp3"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${local.resolved_name}-${var.environment}-final" : null

  deletion_protection = var.environment == "production"

  performance_insights_enabled = var.environment == "production"

  tags = {
    Name        = "${local.resolved_name}-${var.environment}"
    Environment = var.environment
  }
}

# =============================================================================
# Azure Database for PostgreSQL
# =============================================================================

resource "azurerm_postgresql_flexible_server" "postgres" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name                = "${local.resolved_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = local.resolved_location

  version = "15"

  sku_name = var.environment == "production" ? "GP_Standard_D2s_v3" : "B_Standard_B1ms"

  storage_mb = local.resolved_storage_gb * 1024

  administrator_login    = var.username
  administrator_password = var.password

  backup_retention_days = var.backup_retention_days

  geo_redundant_backup_enabled = var.environment == "production"

  zone = local.resolved_multi_az ? "1" : null

  tags = {
    Name        = "${local.resolved_name}-${var.environment}"
    Environment = var.environment
  }
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.postgres[0].id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# =============================================================================
# Google Cloud SQL PostgreSQL
# =============================================================================

resource "google_sql_database_instance" "postgres" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name             = "${local.resolved_name}-${var.environment}"
  project          = local.resolved_project_id
  region           = local.resolved_location
  database_version = "POSTGRES_15"

  deletion_protection = var.environment == "production"

  settings {
    tier = var.environment == "production" ? "db-custom-2-4096" : "db-f1-micro"

    availability_type = local.resolved_multi_az ? "REGIONAL" : "ZONAL"

    disk_size       = local.resolved_storage_gb
    disk_type       = "PD_SSD"
    disk_autoresize = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "production"
      backup_retention_settings {
        retained_backups = var.backup_retention_days
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_name
    }

    maintenance_window {
      day  = 1
      hour = 4
    }

    insights_config {
      query_insights_enabled = var.environment == "production"
    }
  }
}

resource "google_sql_database" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name     = var.database_name
  instance = google_sql_database_instance.postgres[0].name
  project  = local.resolved_project_id
}

resource "google_sql_user" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name     = var.username
  instance = google_sql_database_instance.postgres[0].name
  project  = local.resolved_project_id
  password = var.password
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "host" {
  description = "Database host endpoint"
  value = coalesce(
    try(aws_db_instance.postgres[0].endpoint, ""),
    try(azurerm_postgresql_flexible_server.postgres[0].fqdn, ""),
    try(google_sql_database_instance.postgres[0].private_ip_address, "")
  )
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

output "connection_string" {
  description = "Full connection string (without password)"
  value       = "postgresql://${var.username}@${local.host}:5432/${var.database_name}?sslmode=require"
  sensitive   = false
}

locals {
  host = coalesce(
    try(aws_db_instance.postgres[0].endpoint, ""),
    try(azurerm_postgresql_flexible_server.postgres[0].fqdn, ""),
    try(google_sql_database_instance.postgres[0].private_ip_address, "")
  )
}
