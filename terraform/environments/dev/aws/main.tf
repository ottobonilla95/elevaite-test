# =============================================================================
# Development Environment - AWS
# Shared infrastructure for PR environments (database-per-PR pattern)
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
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket = "elevaite-terraform-state"
    key    = "dev/aws/terraform.tfstate"
    region = "us-west-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "dev"
      Project     = "elevaite"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-1"
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
  description = "Database master password"
  type        = string
  sensitive   = true
}

# =============================================================================
# NETWORKING (Simplified for dev)
# =============================================================================

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "elevaite-dev"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true  # Cost saving for dev

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = "dev"
  }
}

# Security group for databases
resource "aws_security_group" "database" {
  name_prefix = "elevaite-dev-db-"
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
# DATABASE (Shared - PR environments create databases dynamically)
# =============================================================================

module "database" {
  source = "../../../modules/database"

  cloud_provider = "aws"
  environment    = "dev"
  name           = "elevaite"

  instance_class    = "db.t4g.micro"  # Minimum for dev
  allocated_storage = 20
  database_name     = "elevaite_dev"
  username          = "elevaite"
  password          = var.db_password
  multi_az          = false  # Cost saving for dev

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.database.id]
}

# =============================================================================
# OBJECT STORAGE
# =============================================================================

module "storage" {
  source = "../../../modules/storage"

  cloud_provider = "aws"
  environment    = "dev"
  name           = "elevaite"
  bucket_name    = "elevaite-dev-files-${data.aws_caller_identity.current.account_id}"

  enable_versioning = false  # Not needed for dev
}

data "aws_caller_identity" "current" {}

# =============================================================================
# KUBERNETES (Shared dev cluster for PR namespaces)
# =============================================================================

module "kubernetes" {
  source = "../../../modules/kubernetes"

  cloud_provider = "aws"
  environment    = "dev"
  name           = "elevaite"

  kubernetes_version = "1.28"
  node_count         = 2
  min_nodes          = 1
  max_nodes          = 4
  node_instance_type = "t3.medium"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}

# =============================================================================
# DNS (dev.elevaite.ai for PR environments)
# =============================================================================

module "dns" {
  source = "../../../modules/dns"

  cloud_provider = "aws"
  environment    = "dev"
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
  environment       = "dev"
  domain_name       = var.domain_name
  dns_zone_id       = module.dns.dev_zone_id  # Use dev subdomain zone
  letsencrypt_email = var.letsencrypt_email
  aws_region        = var.aws_region
  oidc_provider     = module.kubernetes.oidc_provider

  depends_on = [module.kubernetes]
}

# =============================================================================
# OUTPUTS (Used by CI/CD for PR environments)
# =============================================================================

output "database_host" {
  description = "PostgreSQL host for PR environments"
  value       = module.database.host
}

output "database_port" {
  value = module.database.port
}

output "storage_bucket" {
  value = module.storage.bucket_name
}

output "kubernetes_cluster_name" {
  value = module.kubernetes.cluster_name
}

output "kubernetes_endpoint" {
  value = module.kubernetes.cluster_endpoint
}

output "kubeconfig_command" {
  value = module.kubernetes.kubeconfig_command
}

output "dev_dns_name_servers" {
  description = "Name servers for dev.elevaite.ai - add NS record in main zone"
  value       = module.dns.dev_name_servers
}

# Helm values output (for CI/CD to use)
output "helm_values" {
  description = "Values to pass to Helm for PR deployments"
  value = {
    postgresql_host = module.database.host
    storage_bucket  = module.storage.bucket_name
  }
}
