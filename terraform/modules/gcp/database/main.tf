# =============================================================================
# PostgreSQL Database Module (Google Cloud SQL)
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
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

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "elevaite"
}

variable "username" {
  description = "Database username"
  type        = string
  default     = "elevaite"
}

variable "password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "high_availability" {
  description = "Enable high availability (regional)"
  type        = bool
  default     = false
}

variable "network_name" {
  description = "VPC network name for private IP"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Labels for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "google_sql_database_instance" "main" {
  name             = "${var.name}-${var.environment}"
  project          = var.project_id
  region           = var.region
  database_version = var.database_version

  deletion_protection = var.environment == "production"

  settings {
    tier = var.environment == "production" ? "db-custom-2-4096" : var.tier

    availability_type = var.high_availability ? "REGIONAL" : "ZONAL"

    disk_size       = var.disk_size
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

    dynamic "ip_configuration" {
      for_each = var.network_name != "" ? [1] : []
      content {
        ipv4_enabled    = false
        private_network = var.network_name
      }
    }

    dynamic "ip_configuration" {
      for_each = var.network_name == "" ? [1] : []
      content {
        ipv4_enabled = true
        authorized_networks {
          name  = "all"
          value = "0.0.0.0/0"
        }
      }
    }

    maintenance_window {
      day  = 1
      hour = 4
    }

    insights_config {
      query_insights_enabled = var.environment == "production"
    }

    user_labels = merge(
      {
        environment = var.environment
      },
      var.labels
    )
  }
}

resource "google_sql_database" "main" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

resource "google_sql_user" "main" {
  name     = var.username
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = var.password
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "host" {
  description = "Database host (private IP or public IP)"
  value       = var.network_name != "" ? google_sql_database_instance.main.private_ip_address : google_sql_database_instance.main.public_ip_address
}

output "private_ip" {
  description = "Database private IP address"
  value       = google_sql_database_instance.main.private_ip_address
}

output "public_ip" {
  description = "Database public IP address"
  value       = google_sql_database_instance.main.public_ip_address
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

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}

output "connection_name" {
  description = "Cloud SQL connection name (for Cloud SQL Proxy)"
  value       = google_sql_database_instance.main.connection_name
}

output "self_link" {
  description = "Cloud SQL instance self link"
  value       = google_sql_database_instance.main.self_link
}
