# =============================================================================
# PostgreSQL Database Module (AWS RDS)
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

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "elevaite"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "Storage size in GB"
  type        = number
  default     = 20
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

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
  default     = []
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15"
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

variable "publicly_accessible" {
  description = "Make database publicly accessible (needed for CI/CD in dev)"
  type        = bool
  default     = false
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = merge(
    {
      Name        = "${var.name}-${var.environment}"
      Environment = var.environment
    },
    var.tags
  )
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.name}-${var.environment}"

  engine                = "postgres"
  engine_version        = var.engine_version
  instance_class        = var.instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2

  db_name  = var.database_name
  username = var.username
  password = var.password

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids
  publicly_accessible    = var.publicly_accessible

  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"
  apply_immediately       = var.environment == "dev" ? true : false # Apply changes immediately in dev

  storage_encrypted = true
  storage_type      = "gp3"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.name}-${var.environment}-final" : null

  deletion_protection = var.environment == "production"

  performance_insights_enabled = var.environment == "production"

  tags = merge(
    {
      Name        = "${var.name}-${var.environment}"
      Environment = var.environment
    },
    var.tags
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "host" {
  description = "Database host endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "address" {
  description = "Database address (without port)"
  value       = aws_db_instance.postgres.address
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
  value       = "postgresql://${var.username}@${aws_db_instance.postgres.endpoint}/${var.database_name}?sslmode=require"
}

output "instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.postgres.id
}

output "arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.postgres.arn
}
