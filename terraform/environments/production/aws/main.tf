# =============================================================================
# Production Environment - AWS
# High availability, multi-AZ deployment
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }

  backend "s3" {
    bucket         = "elevaite-terraform-state"
    key            = "production/aws/terraform.tfstate"
    region         = "us-west-1"
    encrypt        = true
    dynamodb_table = "elevaite-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "production"
      Project     = "elevaite"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  type    = string
  default = "us-west-1"
}

variable "domain_name" {
  description = "Domain name (e.g., elevaite.ai)"
  type        = string
  default     = "elevaite.ai"
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt certificates"
  type        = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "pagerduty_service_key" {
  description = "PagerDuty service key for critical alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

variable "rabbitmq_erlang_cookie" {
  description = "RabbitMQ Erlang cookie for cluster communication"
  type        = string
  sensitive   = true
  default     = ""
}

variable "qdrant_api_key" {
  description = "Qdrant API key for authentication"
  type        = string
  sensitive   = true
}

# =============================================================================
# NETWORKING (Production - Multi-AZ)
# =============================================================================

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "elevaite-production"
  cidr = "10.2.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}c"]
  private_subnets = ["10.2.1.0/24", "10.2.2.0/24"]
  public_subnets  = ["10.2.101.0/24", "10.2.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # Cost saving: single NAT

  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Flow Logs for security
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
}

resource "aws_security_group" "database" {
  name_prefix = "elevaite-prod-db-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# DATABASE (Production - Multi-AZ)
# =============================================================================

module "database" {
  source = "../../../modules/aws/database"

  environment = "production"
  name        = "elevaite"

  instance_class    = "db.t4g.micro" # Minimum for cost savings
  allocated_storage = 20
  database_name     = "elevaite"
  username          = "elevaite"
  password          = var.db_password
  multi_az          = false # Cost saving: no Multi-AZ

  backup_retention_days = 30 # Longer retention for production

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.database.id]
}

# =============================================================================
# OBJECT STORAGE (Production - Versioning + Lifecycle)
# =============================================================================

module "storage" {
  source = "../../../modules/aws/storage"

  environment = "production"
  name        = "elevaite"
  bucket_name = "elevaite-production-files-${data.aws_caller_identity.current.account_id}"

  enable_versioning = true
  lifecycle_days    = 90 # Transition to IA after 90 days
}

data "aws_caller_identity" "current" {}

# =============================================================================
# KUBERNETES (Production - HA)
# =============================================================================

module "kubernetes" {
  source = "../../../modules/aws/kubernetes"

  environment = "production"
  name        = "elevaite"

  kubernetes_version = "1.31"
  node_count         = 3
  min_nodes          = 2
  max_nodes          = 5
  node_instance_type = "t3.large" # Production needs more memory for full monitoring stack + application

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}

# =============================================================================
# DNS
# =============================================================================

module "dns" {
  source = "../../../modules/aws/dns"

  environment = "production"
  domain_name = var.domain_name
}

# =============================================================================
# CLUSTER ADD-ONS (Ingress, cert-manager, external-dns)
# =============================================================================

# Providers for Kubernetes/Helm (after cluster is created)
provider "kubernetes" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.kubernetes.cluster_endpoint
    cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
    }
  }
}

provider "kubectl" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_certificate)
  load_config_file       = false
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
  }
}

module "cluster_addons" {
  source = "../../../modules/aws/cluster-addons"

  environment            = "production"
  domain_name            = var.domain_name
  dns_zone_id            = module.dns.zone_id
  letsencrypt_email      = var.letsencrypt_email
  aws_region             = var.aws_region
  oidc_provider          = module.kubernetes.oidc_provider
  rabbitmq_password      = var.rabbitmq_password
  rabbitmq_erlang_cookie = var.rabbitmq_erlang_cookie != "" ? var.rabbitmq_erlang_cookie : random_password.rabbitmq_cookie.result

  # Qdrant disabled - ingestion service not deployed
  qdrant_enabled         = false
  qdrant_api_key         = var.qdrant_api_key

  depends_on = [module.kubernetes]
}

resource "random_password" "rabbitmq_cookie" {
  length  = 32
  special = false
}

# =============================================================================
# MONITORING (Prometheus, Grafana, Loki)
# =============================================================================

module "monitoring" {
  source = "../../../modules/monitoring"

  environment            = "production"
  domain_name            = var.domain_name
  grafana_admin_password = var.grafana_admin_password
  slack_webhook_url      = var.slack_webhook_url
  pagerduty_service_key  = var.pagerduty_service_key
  retention_days         = 30 # 30 days for production

  # Disable caching for current scale (re-enable when traffic increases)
  loki_caching_enabled = false

  depends_on = [module.cluster_addons]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "database_host" {
  value = module.database.host
}

output "storage_bucket" {
  value = module.storage.bucket_name
}

output "kubernetes_cluster_name" {
  value = module.kubernetes.cluster_name
}

output "kubeconfig_command" {
  value = module.kubernetes.kubeconfig_command
}

output "grafana_url" {
  value = module.monitoring.grafana_url
}

output "dns_name_servers" {
  description = "Update your domain registrar with these name servers"
  value       = module.dns.name_servers
}

output "helm_values" {
  value = {
    postgresql_host = module.database.host
    storage_bucket  = module.storage.bucket_name
    qdrant_host     = module.cluster_addons.qdrant_host
    rabbitmq_host   = module.cluster_addons.rabbitmq_host
  }
}

output "qdrant_host" {
  value = module.cluster_addons.qdrant_host
}

output "rabbitmq_host" {
  value = module.cluster_addons.rabbitmq_host
}
