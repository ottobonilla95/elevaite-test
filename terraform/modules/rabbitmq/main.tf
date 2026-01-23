# =============================================================================
# RabbitMQ Module (Multi-Cloud)
# Provisions managed RabbitMQ: CloudAMQP (multi-cloud) or Amazon MQ
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudamqp = {
      source  = "cloudamqp/cloudamqp"
      version = "~> 1.28"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "provider_type" {
  description = "RabbitMQ provider: cloudamqp (multi-cloud) or amazon_mq (AWS only)"
  type        = string
  default     = "cloudamqp"
  validation {
    condition     = contains(["cloudamqp", "amazon_mq"], var.provider_type)
    error_message = "provider_type must be one of: cloudamqp, amazon_mq"
  }
}

variable "cloud_region" {
  description = "Cloud region for CloudAMQP: amazon-web-services::us-east-1, azure-arm::eastus, google-compute-engine::us-central1"
  type        = string
  default     = "amazon-web-services::us-east-1"
}

# Alias for multi-cloud compatibility
variable "region" {
  description = "Alias for cloud_region (multi-cloud compatibility)"
  type        = string
  default     = ""
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

variable "plan" {
  description = "CloudAMQP plan: lemur (free), tiger, bunny, rabbit, panda"
  type        = string
  default     = "lemur"
}

variable "username" {
  description = "RabbitMQ username"
  type        = string
  default     = "elevaite"
}

variable "password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

# AWS specific (for Amazon MQ)
variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
  default     = []
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

  # Resolve region (region alias)
  resolved_region = var.region != "" ? var.region : var.cloud_region
}

# =============================================================================
# CloudAMQP (Multi-Cloud: AWS, Azure, GCP)
# =============================================================================

resource "cloudamqp_instance" "rabbitmq" {
  count = var.provider_type == "cloudamqp" ? 1 : 0

  name   = "${local.resolved_name}-${var.environment}"
  plan   = var.plan
  region = local.resolved_region

  tags = concat([var.environment, local.resolved_name], [for k, v in var.tags : "${k}=${v}"])

  # Enable for production
  no_default_alarms = var.environment != "production"
}

# Create vhosts for different environments/PRs
resource "cloudamqp_vhost" "main" {
  count = var.provider_type == "cloudamqp" ? 1 : 0

  instance_id = cloudamqp_instance.rabbitmq[0].id
  name        = var.environment
}

# =============================================================================
# Amazon MQ (AWS Only)
# =============================================================================

resource "aws_mq_broker" "rabbitmq" {
  count = var.provider_type == "amazon_mq" ? 1 : 0

  broker_name = "${local.resolved_name}-${var.environment}"

  engine_type        = "RabbitMQ"
  engine_version     = "3.11"
  host_instance_type = var.environment == "production" ? "mq.m5.large" : "mq.t3.micro"
  deployment_mode    = var.environment == "production" ? "CLUSTER_MULTI_AZ" : "SINGLE_INSTANCE"

  publicly_accessible = false
  subnet_ids          = var.environment == "production" ? var.subnet_ids : [var.subnet_ids[0]]
  security_groups     = var.security_group_ids

  user {
    username = var.username
    password = var.password
  }

  auto_minor_version_upgrade = true

  logs {
    general = true
  }

  tags = merge(
    {
      Name        = "${local.resolved_name}-${var.environment}"
      Environment = var.environment
    },
    var.tags
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "host" {
  description = "RabbitMQ host endpoint"
  value = coalesce(
    try(cloudamqp_instance.rabbitmq[0].host, ""),
    try(aws_mq_broker.rabbitmq[0].instances[0].endpoints[0], "")
  )
}

output "port" {
  description = "RabbitMQ AMQP port"
  value       = 5672
}

output "amqp_url" {
  description = "Full AMQP connection URL"
  value = var.provider_type == "cloudamqp" ? (
    try(cloudamqp_instance.rabbitmq[0].url, "")
  ) : (
    "amqps://${var.username}@${try(aws_mq_broker.rabbitmq[0].instances[0].endpoints[0], "")}:5671"
  )
  sensitive = true
}

output "management_url" {
  description = "RabbitMQ Management UI URL"
  value = var.provider_type == "cloudamqp" ? (
    "https://${try(cloudamqp_instance.rabbitmq[0].host, "")}"
  ) : (
    try(aws_mq_broker.rabbitmq[0].instances[0].console_url, "")
  )
}

output "vhost" {
  description = "Default vhost name"
  value       = var.environment
}
