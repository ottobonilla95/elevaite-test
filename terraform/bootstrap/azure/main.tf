# =============================================================================
# Terraform Bootstrap - Azure
# Creates Storage Account and Container for Terraform state management
# Run this ONCE before using other Terraform configurations
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "elevaite"
}

# =============================================================================
# RESOURCE GROUP
# =============================================================================

resource "azurerm_resource_group" "terraform" {
  name     = "${var.project_name}-terraform-state"
  location = var.location

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform-bootstrap"
  }
}

# =============================================================================
# STORAGE ACCOUNT FOR STATE
# =============================================================================

resource "azurerm_storage_account" "terraform" {
  name                     = "${replace(var.project_name, "-", "")}tfstate"
  resource_group_name      = azurerm_resource_group.terraform.name
  location                 = azurerm_resource_group.terraform.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  min_tls_version = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform-bootstrap"
  }
}

resource "azurerm_storage_container" "terraform" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.terraform.name
  container_access_type = "private"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "resource_group_name" {
  description = "Resource group for Terraform state"
  value       = azurerm_resource_group.terraform.name
}

output "storage_account_name" {
  description = "Storage account for Terraform state"
  value       = azurerm_storage_account.terraform.name
}

output "container_name" {
  description = "Container for Terraform state"
  value       = azurerm_storage_container.terraform.name
}

output "backend_config" {
  description = "Backend configuration to use in other Terraform configs"
  value       = <<-EOT
    terraform {
      backend "azurerm" {
        resource_group_name  = "${azurerm_resource_group.terraform.name}"
        storage_account_name = "${azurerm_storage_account.terraform.name}"
        container_name       = "${azurerm_storage_container.terraform.name}"
        key                  = "ENV/azure/terraform.tfstate"  # Replace ENV with dev/staging/production
      }
    }
  EOT
}
