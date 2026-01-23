# =============================================================================
# Staging Environment - AWS
# Production-like environment with smaller resources
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
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket = "elevaite-terraform-state"
    key    = "staging/aws/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "staging"
      Project     = "elevaite"
      ManagedBy   = "terraform"
    }
  }
}

provider "cloudamqp" {
  apikey = var.cloudamqp_api_key
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  type    = string
  default = "us-east-1"
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

variable "cloudamqp_api_key" {
  type      = string
  sensitive = true
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

# =============================================================================
# NETWORKING
# =============================================================================

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "elevaite-staging"
  cidr = "10.1.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  public_subnets  = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true  # Cost saving for staging

  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_security_group" "database" {
  name_prefix = "elevaite-staging-db-"
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
}

# =============================================================================
# DATABASE
# =============================================================================

module "database" {
  source = "../../../modules/database"

  cloud_provider = "aws"
  environment    = "staging"
  name           = "elevaite"

  instance_class    = "db.t4g.micro"  # Cheapest option (ARM-based)
  allocated_storage = 20              # Minimum storage
  database_name     = "elevaite_staging"
  username          = "elevaite"
  password          = var.db_password
  multi_az          = false

  backup_retention_days = 7

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.database.id]
}

# =============================================================================
# RABBITMQ
# =============================================================================

module "rabbitmq" {
  source = "../../../modules/rabbitmq"

  provider_type = "cloudamqp"
  cloud_region  = "amazon-web-services::${var.aws_region}"
  environment   = "staging"
  name          = "elevaite"

  plan = "lemur"  # Free tier - cheapest option
}

# =============================================================================
# OBJECT STORAGE
# =============================================================================

module "storage" {
  source = "../../../modules/storage"

  cloud_provider = "aws"
  environment    = "staging"
  name           = "elevaite"
  bucket_name    = "elevaite-staging-files-${data.aws_caller_identity.current.account_id}"

  enable_versioning = true
}

data "aws_caller_identity" "current" {}

# =============================================================================
# KUBERNETES
# =============================================================================

module "kubernetes" {
  source = "../../../modules/kubernetes"

  cloud_provider = "aws"
  environment    = "staging"
  name           = "elevaite"

  kubernetes_version = "1.28"
  node_count         = 2           # Minimum for EKS
  min_nodes          = 2
  max_nodes          = 3           # Limited scaling
  node_instance_type = "t3.small"  # Cheapest viable option

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}

# =============================================================================
# DNS
# =============================================================================

module "dns" {
  source = "../../../modules/dns"

  cloud_provider = "aws"
  environment    = "staging"
  domain_name    = var.domain_name
}

# =============================================================================
# CLUSTER ADD-ONS (Ingress, cert-manager, external-dns)
# =============================================================================

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

module "cluster_addons" {
  source = "../../../modules/cluster-addons"

  cloud_provider    = "aws"
  environment       = "staging"
  domain_name       = var.domain_name
  dns_zone_id       = module.dns.zone_id
  letsencrypt_email = var.letsencrypt_email
  aws_region        = var.aws_region
  oidc_provider     = module.kubernetes.oidc_provider

  depends_on = [module.kubernetes]
}

# =============================================================================
# MONITORING (Prometheus, Grafana, Loki)
# =============================================================================

module "monitoring" {
  source = "../../../modules/monitoring"

  environment            = "staging"
  domain_name            = var.domain_name
  grafana_admin_password = var.grafana_admin_password
  slack_webhook_url      = var.slack_webhook_url
  retention_days         = 15  # 15 days for staging

  depends_on = [module.cluster_addons]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "database_host" {
  value = module.database.host
}

output "rabbitmq_host" {
  value = module.rabbitmq.host
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

output "helm_values" {
  value = {
    postgresql_host = module.database.host
    rabbitmq_host   = module.rabbitmq.host
    storage_bucket  = module.storage.bucket_name
  }
}
