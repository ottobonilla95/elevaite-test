# =============================================================================
# Kubernetes Cluster Module (Azure AKS)
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

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "name" {
  description = "Cluster name prefix"
  type        = string
  default     = "elevaite"
}

variable "cluster_name" {
  description = "Full cluster name (overrides name-environment pattern)"
  type        = string
  default     = ""
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "node_count" {
  description = "Desired number of nodes"
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

variable "vm_size" {
  description = "VM size for nodes"
  type        = string
  default     = "Standard_B2s"
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.name}-${var.environment}"
}

# =============================================================================
# RESOURCES
# =============================================================================

resource "azurerm_kubernetes_cluster" "main" {
  name                = local.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = local.cluster_name
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
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
      Name        = local.cluster_name
      Environment = var.environment
    },
    var.tags
  )
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.main.name
}

output "cluster_endpoint" {
  description = "AKS cluster endpoint"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].host
}

output "cluster_ca_certificate" {
  description = "AKS cluster CA certificate (base64 encoded)"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "az aks get-credentials --resource-group ${var.resource_group_name} --name ${azurerm_kubernetes_cluster.main.name}"
}

output "kube_config_raw" {
  description = "Raw kubeconfig"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "client_certificate" {
  description = "Client certificate"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].client_certificate
  sensitive   = true
}

output "client_key" {
  description = "Client key"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].client_key
  sensitive   = true
}

output "cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.main.id
}

output "identity_principal_id" {
  description = "System assigned identity principal ID"
  value       = azurerm_kubernetes_cluster.main.identity[0].principal_id
}

output "kubelet_identity_object_id" {
  description = "Kubelet managed identity object ID"
  value       = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}
