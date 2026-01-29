# =============================================================================
# DNS Module (AWS Route53)
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
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

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = merge(
    {
      Name        = var.domain_name
      Environment = var.environment
    },
    var.tags
  )
}

# Wildcard for PR environments (*.dev.domain.com)
resource "aws_route53_zone" "dev" {
  count = var.environment == "dev" ? 1 : 0

  name = "dev.${var.domain_name}"

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
resource "aws_route53_record" "dev_ns_delegation" {
  count   = var.environment == "dev" ? 1 : 0
  zone_id = aws_route53_zone.main.zone_id
  name    = "dev.${var.domain_name}"
  type    = "NS"
  ttl     = 300
  records = aws_route53_zone.dev[0].name_servers
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "zone_id" {
  description = "Route53 Zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "zone_name" {
  description = "Route53 Zone name"
  value       = aws_route53_zone.main.name
}

output "name_servers" {
  description = "Name servers for the zone (update your registrar with these)"
  value       = aws_route53_zone.main.name_servers
}

output "zone_arn" {
  description = "Route53 Zone ARN"
  value       = aws_route53_zone.main.arn
}

output "dev_zone_id" {
  description = "Dev Route53 Zone ID (for PR environments)"
  value       = var.environment == "dev" ? aws_route53_zone.dev[0].zone_id : ""
}

output "dev_name_servers" {
  description = "Dev zone name servers"
  value       = var.environment == "dev" ? aws_route53_zone.dev[0].name_servers : []
}
