# =============================================================================
# DNS Module (Azure DNS)
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

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "azurerm_dns_zone" "main" {
  name                = var.domain_name
  resource_group_name = var.resource_group_name

  tags = merge(
    {
      Name        = var.domain_name
      Environment = var.environment
    },
    var.tags
  )
}

# Wildcard for PR environments (*.dev.domain.com)
resource "azurerm_dns_zone" "dev" {
  count = var.environment == "dev" ? 1 : 0

  name                = "dev.${var.domain_name}"
  resource_group_name = var.resource_group_name

  tags = merge(
    {
      Name        = "dev.${var.domain_name}"
      Environment = "dev"
    },
    var.tags
  )
}

# NS delegation from main zone to dev zone
# This allows dev.elevaite.ai to be resolved via the dev zone's nameservers
resource "azurerm_dns_ns_record" "dev_ns_delegation" {
  count               = var.environment == "dev" ? 1 : 0
  name                = "dev"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = azurerm_dns_zone.dev[0].name_servers
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "zone_id" {
  description = "Azure DNS Zone ID"
  value       = azurerm_dns_zone.main.id
}

output "zone_name" {
  description = "Azure DNS Zone name"
  value       = azurerm_dns_zone.main.name
}

output "name_servers" {
  description = "Name servers for the zone (update your registrar with these)"
  value       = azurerm_dns_zone.main.name_servers
}

output "dev_zone_id" {
  description = "Dev DNS Zone ID (for PR environments)"
  value       = var.environment == "dev" ? azurerm_dns_zone.dev[0].id : ""
}

output "dev_name_servers" {
  description = "Dev zone name servers"
  value       = var.environment == "dev" ? azurerm_dns_zone.dev[0].name_servers : []
}
