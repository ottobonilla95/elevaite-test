# =============================================================================
# Kubernetes Cluster Module (Multi-Cloud)
# Provisions managed K8s: AWS EKS, Azure AKS, Google GKE
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

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Cluster name prefix"
  type        = string
  default     = "elevaite"
}

# Alias for multi-cloud compatibility
variable "project_name" {
  description = "Alias for name (multi-cloud compatibility)"
  type        = string
  default     = ""
}

variable "cluster_name" {
  description = "Full cluster name (overrides name-environment pattern)"
  type        = string
  default     = ""
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_count" {
  description = "Number of nodes"
  type        = number
  default     = 2
}

variable "min_nodes" {
  description = "Minimum nodes for autoscaling"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum nodes for autoscaling"
  type        = number
  default     = 5
}

variable "node_instance_type" {
  description = "Node instance type"
  type        = string
  default     = "t3.medium"
}

variable "node_pools" {
  description = "Map of node pool configurations (advanced multi-cloud)"
  type        = any
  default     = {}
}

# Networking
variable "vpc_id" {
  description = "VPC ID (AWS)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []
}

# Azure specific
variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = ""
}

variable "location" {
  description = "Azure/GCP region"
  type        = string
  default     = "eastus"
}

# Alias for multi-cloud compatibility
variable "region" {
  description = "Alias for location (multi-cloud compatibility)"
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

variable "network_name" {
  description = "GCP VPC network name"
  type        = string
  default     = ""
}

variable "network" {
  description = "Alias for network_name (GCP compatibility)"
  type        = string
  default     = ""
}

variable "subnetwork_name" {
  description = "GCP subnetwork name"
  type        = string
  default     = ""
}

variable "subnetwork" {
  description = "Alias for subnetwork_name (GCP compatibility)"
  type        = string
  default     = ""
}

variable "regional" {
  description = "Create regional cluster (GCP)"
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels/tags for resources (GCP/Azure)"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS - Resolve variable aliases for multi-cloud compatibility
# =============================================================================

locals {
  # Resolve name (project_name alias or cluster_name override)
  resolved_name = (
    var.cluster_name != "" ? var.cluster_name :
    var.project_name != "" ? var.project_name :
    var.name
  )

  # Resolve location (region alias)
  resolved_location = var.region != "" ? var.region : var.location

  # Resolve GCP project ID (gcp_project_id alias)
  resolved_project_id = var.gcp_project_id != "" ? var.gcp_project_id : var.project_id

  # Resolve GCP network (network alias)
  resolved_network = var.network != "" ? var.network : var.network_name

  # Resolve GCP subnetwork (subnetwork alias)
  resolved_subnetwork = var.subnetwork != "" ? var.subnetwork : var.subnetwork_name
}

# =============================================================================
# AWS EKS
# =============================================================================

resource "aws_eks_cluster" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name     = local.resolved_name
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = var.environment != "production"
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  tags = {
    Name        = local.resolved_name
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]
}

resource "aws_eks_node_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  cluster_name    = aws_eks_cluster.main[0].name
  node_group_name = "${var.name}-${var.environment}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes[0].arn
  subnet_ids      = var.subnet_ids

  instance_types = [var.node_instance_type]

  scaling_config {
    desired_size = var.node_count
    min_size     = var.min_nodes
    max_size     = var.max_nodes
  }

  update_config {
    max_unavailable = 1
  }

  tags = {
    Name        = "${var.name}-${var.environment}-nodes"
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry,
  ]
}

# OIDC Provider for EKS (required for IRSA - IAM Roles for Service Accounts)
data "tls_certificate" "eks" {
  count = var.cloud_provider == "aws" ? 1 : 0
  url   = aws_eks_cluster.main[0].identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  count = var.cloud_provider == "aws" ? 1 : 0

  url = aws_eks_cluster.main[0].identity[0].oidc[0].issuer

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [data.tls_certificate.eks[0].certificates[0].sha1_fingerprint]

  tags = {
    Name        = "${var.name}-${var.environment}-eks-oidc"
    Environment = var.environment
  }
}

# EKS IAM Roles
resource "aws_iam_role" "eks_cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = "${var.name}-${var.environment}-eks-cluster"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster[0].name
}

resource "aws_iam_role" "eks_nodes" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = "${var.name}-${var.environment}-eks-nodes"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes[0].name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes[0].name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes[0].name
}

# =============================================================================
# Azure AKS
# =============================================================================

resource "azurerm_kubernetes_cluster" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0

  name                = local.resolved_name
  location            = local.resolved_location
  resource_group_name = var.resource_group_name
  dns_prefix          = local.resolved_name
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.node_instance_type
    enable_auto_scaling = true
    min_count           = var.min_nodes
    max_count           = var.max_nodes
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }

  tags = merge(
    {
      Name        = local.resolved_name
      Environment = var.environment
    },
    var.labels
  )
}

# =============================================================================
# Google GKE
# =============================================================================

resource "google_container_cluster" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name     = local.resolved_name
  project  = local.resolved_project_id
  location = local.resolved_location

  min_master_version = var.kubernetes_version

  # We can't create a cluster with no node pool, but we want to manage them separately
  # So we create the smallest possible default pool and immediately delete it
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = local.resolved_network
  subnetwork = local.resolved_subnetwork

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = var.environment == "production"
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  workload_identity_config {
    workload_pool = "${local.resolved_project_id}.svc.id.goog"
  }

  resource_labels = var.labels
}

resource "google_container_node_pool" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  name     = "${local.resolved_name}-pool"
  project  = local.resolved_project_id
  location = local.resolved_location
  cluster  = google_container_cluster.main[0].name

  initial_node_count = var.node_count

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  node_config {
    machine_type = var.node_instance_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = var.environment
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cluster_name" {
  description = "Kubernetes cluster name"
  value = coalesce(
    try(aws_eks_cluster.main[0].name, ""),
    try(azurerm_kubernetes_cluster.main[0].name, ""),
    try(google_container_cluster.main[0].name, "")
  )
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint"
  value = coalesce(
    try(aws_eks_cluster.main[0].endpoint, ""),
    try(azurerm_kubernetes_cluster.main[0].kube_config[0].host, ""),
    try("https://${google_container_cluster.main[0].endpoint}", "")
  )
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate"
  value = coalesce(
    try(aws_eks_cluster.main[0].certificate_authority[0].data, ""),
    try(azurerm_kubernetes_cluster.main[0].kube_config[0].cluster_ca_certificate, ""),
    try(google_container_cluster.main[0].master_auth[0].cluster_ca_certificate, "")
  )
  sensitive = true
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value = var.cloud_provider == "aws" ? (
    "aws eks update-kubeconfig --name ${try(aws_eks_cluster.main[0].name, "")} --region ${data.aws_region.current[0].name}"
  ) : var.cloud_provider == "azure" ? (
    "az aks get-credentials --resource-group ${var.resource_group_name} --name ${try(azurerm_kubernetes_cluster.main[0].name, "")}"
  ) : (
    "gcloud container clusters get-credentials ${try(google_container_cluster.main[0].name, "")} --region ${var.location} --project ${var.project_id}"
  )
}

output "oidc_provider" {
  description = "OIDC provider URL for AWS EKS (for IRSA)"
  value = var.cloud_provider == "aws" ? (
    try(replace(aws_eks_cluster.main[0].identity[0].oidc[0].issuer, "https://", ""), "")
  ) : ""
}

output "oidc_provider_arn" {
  description = "OIDC provider ARN for AWS EKS"
  value = var.cloud_provider == "aws" ? (
    try(aws_iam_openid_connect_provider.eks[0].arn, "")
  ) : ""
}

data "aws_region" "current" {
  count = var.cloud_provider == "aws" ? 1 : 0
}
