# =============================================================================
# DNS Module (Google Cloud DNS)
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

variable "domain_name" {
  description = "Domain name (e.g., elevaite.ai)"
  type        = string
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

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "labels" {
  description = "Labels for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "google_dns_managed_zone" "main" {
  name        = replace(var.domain_name, ".", "-")
  dns_name    = "${var.domain_name}."
  project     = var.project_id
  description = "DNS zone for ${var.domain_name}"

  labels = merge(
    {
      environment = var.environment
    },
    { for k, v in var.labels : k => replace(lower(v), "/[^a-z0-9_-]/", "_") }
  )
}

# Wildcard for PR environments (*.dev.domain.com)
resource "google_dns_managed_zone" "dev" {
  count = var.environment == "dev" ? 1 : 0

  name        = "dev-${replace(var.domain_name, ".", "-")}"
  dns_name    = "dev.${var.domain_name}."
  project     = var.project_id
  description = "DNS zone for dev.${var.domain_name}"

  labels = merge(
    {
      environment = "dev"
    },
    { for k, v in var.labels : k => replace(lower(v), "/[^a-z0-9_-]/", "_") }
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "zone_id" {
  description = "Cloud DNS Zone ID"
  value       = google_dns_managed_zone.main.id
}

output "zone_name" {
  description = "Cloud DNS Zone name"
  value       = google_dns_managed_zone.main.name
}

output "dns_name" {
  description = "Cloud DNS Zone DNS name"
  value       = google_dns_managed_zone.main.dns_name
}

output "name_servers" {
  description = "Name servers for the zone (update your registrar with these)"
  value       = google_dns_managed_zone.main.name_servers
}

output "dev_zone_id" {
  description = "Dev DNS Zone ID (for PR environments)"
  value       = var.environment == "dev" ? google_dns_managed_zone.dev[0].id : ""
}

output "dev_name_servers" {
  description = "Dev zone name servers"
  value       = var.environment == "dev" ? google_dns_managed_zone.dev[0].name_servers : []
}
