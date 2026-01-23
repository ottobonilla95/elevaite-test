# =============================================================================
# Kubernetes Cluster Add-ons Module
# Deploys: Ingress Controller, cert-manager, external-dns
# These are required for the application to receive traffic with SSL
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
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

variable "domain_name" {
  description = "Domain name (e.g., elevaite.ai)"
  type        = string
}

variable "dns_zone_id" {
  description = "DNS Zone ID for external-dns"
  type        = string
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt certificate notifications"
  type        = string
}

# AWS specific
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-1"
}

variable "oidc_provider" {
  description = "EKS OIDC provider URL (without https://)"
  type        = string
  default     = ""
}

# GCP specific
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = ""
}

# Azure specific
variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = ""
}

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  default     = ""
}

# =============================================================================
# NAMESPACES
# =============================================================================

resource "kubernetes_namespace" "ingress_nginx" {
  metadata {
    name = "ingress-nginx"
  }
}

resource "kubernetes_namespace" "cert_manager" {
  metadata {
    name = "cert-manager"
  }
}

resource "kubernetes_namespace" "external_dns" {
  metadata {
    name = "external-dns"
  }
}

# =============================================================================
# AWS IAM ROLE FOR EXTERNAL-DNS (IRSA - IAM Roles for Service Accounts)
# =============================================================================

data "aws_caller_identity" "current" {
  count = var.cloud_provider == "aws" ? 1 : 0
}

data "aws_iam_policy_document" "external_dns_assume_role" {
  count = var.cloud_provider == "aws" ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current[0].account_id}:oidc-provider/${var.oidc_provider}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider}:sub"
      values   = ["system:serviceaccount:external-dns:external-dns"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "external_dns" {
  count = var.cloud_provider == "aws" ? 1 : 0

  statement {
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListResourceRecordSets"
    ]
    resources = ["arn:aws:route53:::hostedzone/${var.dns_zone_id}"]
  }

  statement {
    actions = [
      "route53:ListHostedZones",
      "route53:ListResourceRecordSets"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "external_dns" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name               = "external-dns-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.external_dns_assume_role[0].json

  tags = {
    Name        = "external-dns-${var.environment}"
    Environment = var.environment
    Service     = "external-dns"
  }
}

resource "aws_iam_role_policy" "external_dns" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name   = "external-dns-policy"
  role   = aws_iam_role.external_dns[0].id
  policy = data.aws_iam_policy_document.external_dns[0].json
}

# =============================================================================
# NGINX INGRESS CONTROLLER
# =============================================================================

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.9.0"
  namespace  = kubernetes_namespace.ingress_nginx.metadata[0].name

  values = [
    yamlencode({
      controller = {
        replicaCount = var.environment == "production" ? 2 : 1
        
        service = {
          annotations = var.cloud_provider == "aws" ? {
            "service.beta.kubernetes.io/aws-load-balancer-type"            = "nlb"
            "service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled" = "true"
          } : var.cloud_provider == "gcp" ? {
            "cloud.google.com/neg" = "{\"ingress\": true}"
          } : {}
        }

        metrics = {
          enabled = true
          serviceMonitor = {
            enabled = true
          }
        }

        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "512Mi"
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.ingress_nginx]
}

# =============================================================================
# CERT-MANAGER (Automatic SSL Certificates)
# =============================================================================

resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  version    = "1.14.0"
  namespace  = kubernetes_namespace.cert_manager.metadata[0].name

  set {
    name  = "installCRDs"
    value = "true"
  }

  values = [
    yamlencode({
      prometheus = {
        enabled = true
        servicemonitor = {
          enabled = true
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.cert_manager]
}

# Let's Encrypt ClusterIssuer (Staging - for testing)
resource "kubernetes_manifest" "letsencrypt_staging" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = "letsencrypt-staging"
    }
    spec = {
      acme = {
        server = "https://acme-staging-v02.api.letsencrypt.org/directory"
        email  = var.letsencrypt_email
        privateKeySecretRef = {
          name = "letsencrypt-staging-key"
        }
        solvers = [{
          http01 = {
            ingress = {
              class = "nginx"
            }
          }
        }]
      }
    }
  }

  depends_on = [helm_release.cert_manager]
}

# Let's Encrypt ClusterIssuer (Production)
resource "kubernetes_manifest" "letsencrypt_prod" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = "letsencrypt-prod"
    }
    spec = {
      acme = {
        server = "https://acme-v02.api.letsencrypt.org/directory"
        email  = var.letsencrypt_email
        privateKeySecretRef = {
          name = "letsencrypt-prod-key"
        }
        solvers = [{
          http01 = {
            ingress = {
              class = "nginx"
            }
          }
        }]
      }
    }
  }

  depends_on = [helm_release.cert_manager]
}

# =============================================================================
# EXTERNAL-DNS (Automatic DNS Record Creation)
# =============================================================================

resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns"
  chart      = "external-dns"
  version    = "1.14.0"
  namespace  = kubernetes_namespace.external_dns.metadata[0].name

  values = [
    yamlencode({
      provider = var.cloud_provider == "aws" ? "aws" : var.cloud_provider == "azure" ? "azure" : "google"

      # AWS specific
      aws = var.cloud_provider == "aws" ? {
        region  = var.aws_region
        zoneType = "public"
      } : null

      # Azure specific
      azure = var.cloud_provider == "azure" ? {
        resourceGroup  = var.resource_group_name
        subscriptionId = var.subscription_id
      } : null

      # GCP specific
      google = var.cloud_provider == "gcp" ? {
        project = var.project_id
      } : null

      domainFilters = [var.domain_name]
      
      policy = "sync"  # sync = create and delete records
      
      sources = ["ingress", "service"]

      txtOwnerId = "${var.environment}-elevaite"

      serviceAccount = {
        create = true
        annotations = var.cloud_provider == "aws" ? {
          "eks.amazonaws.com/role-arn" = aws_iam_role.external_dns[0].arn
        } : {}
      }
    })
  ]

  depends_on = [
    kubernetes_namespace.external_dns,
    aws_iam_role.external_dns
  ]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "ingress_controller_service" {
  description = "Ingress controller service name"
  value       = "ingress-nginx-controller"
}

output "ingress_namespace" {
  description = "Ingress controller namespace"
  value       = kubernetes_namespace.ingress_nginx.metadata[0].name
}

output "cert_manager_namespace" {
  description = "Cert-manager namespace"
  value       = kubernetes_namespace.cert_manager.metadata[0].name
}

output "cluster_issuers" {
  description = "Available ClusterIssuers"
  value       = ["letsencrypt-staging", "letsencrypt-prod"]
}
