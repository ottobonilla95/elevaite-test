# =============================================================================
# DNS Module (Multi-Cloud)
# Provisions DNS zones: AWS Route53, Azure DNS, Google Cloud DNS
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
}

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

# Alias for multi-cloud compatibility
variable "project_name" {
  description = "Alias for name (multi-cloud compatibility)"
  type        = string
  default     = ""
}

# Azure specific
variable "resource_group_name" {
  description = "Azure Resource Group name"
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

variable "tags" {
  description = "Tags/labels for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS - Resolve variable aliases for multi-cloud compatibility
# =============================================================================

locals {
  # Resolve name (project_name alias)
  resolved_name = var.project_name != "" ? var.project_name : var.name

  # Resolve GCP project ID (gcp_project_id alias)
  resolved_project_id = var.gcp_project_id != "" ? var.gcp_project_id : var.project_id
}

# =============================================================================
# AWS Route53
# =============================================================================

resource "aws_route53_zone" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = var.domain_name

  tags = {
    Name        = var.domain_name
    Environment = var.environment
  }
}

# Wildcard for PR environments (*.dev.elevaite.ai)
resource "aws_route53_zone" "dev" {
  count = var.cloud_provider == "aws" && var.environment == "dev" ? 1 : 0

  name = "dev.${var.domain_name}"

  tags = {
    Name        = "dev.${var.domain_name}"
    Environment = "dev"
  }
}

# =============================================================================
# Azure DNS
# =============================================================================

resource "azurerm_dns_zone" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name                = var.domain_name
  resource_group_name = var.resource_group_name

  tags = {
    Name        = var.domain_name
    Environment = var.environment
  }
}

resource "azurerm_dns_zone" "dev" {
  count = var.cloud_provider == "azure" && var.environment == "dev" ? 1 : 0

  name                = "dev.${var.domain_name}"
  resource_group_name = var.resource_group_name

  tags = {
    Name        = "dev.${var.domain_name}"
    Environment = "dev"
  }
}

# =============================================================================
# Google Cloud DNS
# =============================================================================

resource "google_dns_managed_zone" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name        = replace(var.domain_name, ".", "-")
  dns_name    = "${var.domain_name}."
  project     = local.resolved_project_id
  description = "DNS zone for ${var.domain_name}"

  labels = merge(
    {
      environment = var.environment
    },
    { for k, v in var.tags : k => replace(v, "/[^a-z0-9_-]/", "_") }
  )
}

resource "google_dns_managed_zone" "dev" {
  count = var.cloud_provider == "gcp" && var.environment == "dev" ? 1 : 0

  name        = "dev-${replace(var.domain_name, ".", "-")}"
  dns_name    = "dev.${var.domain_name}."
  project     = local.resolved_project_id
  description = "DNS zone for dev.${var.domain_name}"

  labels = merge(
    {
      environment = "dev"
    },
    { for k, v in var.tags : k => replace(v, "/[^a-z0-9_-]/", "_") }
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "zone_id" {
  description = "DNS Zone ID"
  value = coalesce(
    try(aws_route53_zone.main[0].zone_id, ""),
    try(azurerm_dns_zone.main[0].id, ""),
    try(google_dns_managed_zone.main[0].id, "")
  )
}

output "name_servers" {
  description = "Name servers for the zone (update your registrar with these)"
  value = coalesce(
    try(aws_route53_zone.main[0].name_servers, []),
    try(azurerm_dns_zone.main[0].name_servers, []),
    try(google_dns_managed_zone.main[0].name_servers, [])
  )
}

output "dev_zone_id" {
  description = "Dev DNS Zone ID (for PR environments)"
  value = coalesce(
    try(aws_route53_zone.dev[0].zone_id, ""),
    try(azurerm_dns_zone.dev[0].id, ""),
    try(google_dns_managed_zone.dev[0].id, "")
  )
}

output "dev_name_servers" {
  description = "Dev zone name servers"
  value = coalesce(
    try(aws_route53_zone.dev[0].name_servers, []),
    try(azurerm_dns_zone.dev[0].name_servers, []),
    try(google_dns_managed_zone.dev[0].name_servers, [])
  )
}

output "zone_name" {
  description = "DNS Zone name (for external-dns integration)"
  value = coalesce(
    try(aws_route53_zone.main[0].name, ""),
    try(azurerm_dns_zone.main[0].name, ""),
    try(google_dns_managed_zone.main[0].name, "")
  )
}
