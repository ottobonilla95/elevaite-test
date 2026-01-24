# =============================================================================
# Kubernetes Cluster Add-ons Module (Azure)
# Deploys: Ingress Controller, cert-manager, external-dns
# These are required for the application to receive traffic with SSL
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
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

variable "domain_name" {
  description = "Domain name (e.g., elevaite.ai)"
  type        = string
}

variable "dns_zone_name" {
  description = "Azure DNS Zone name for external-dns"
  type        = string
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt certificate notifications"
  type        = string
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
}

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  default     = ""
}

variable "kubelet_identity_client_id" {
  description = "Kubelet managed identity client ID for workload identity"
  type        = string
  default     = ""
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
}

variable "qdrant_api_key" {
  description = "Qdrant API key for authentication"
  type        = string
  sensitive   = true
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

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

# =============================================================================
# PROMETHEUS OPERATOR CRDs (Required for ServiceMonitor resources)
# =============================================================================

resource "helm_release" "prometheus_operator_crds" {
  name       = "prometheus-operator-crds"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-operator-crds"
  version    = "16.0.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  depends_on = [kubernetes_namespace.monitoring]
}

# =============================================================================
# NGINX INGRESS CONTROLLER
# =============================================================================

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.12.0"
  namespace  = kubernetes_namespace.ingress_nginx.metadata[0].name

  values = [
    yamlencode({
      controller = {
        replicaCount = var.environment == "production" ? 2 : 1

        service = {
          annotations = {
            "service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path" = "/healthz"
          }
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

  depends_on = [kubernetes_namespace.ingress_nginx, helm_release.prometheus_operator_crds]
}

# =============================================================================
# CERT-MANAGER (Automatic SSL Certificates)
# =============================================================================

resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  version    = "1.16.2"
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

  depends_on = [kubernetes_namespace.cert_manager, helm_release.prometheus_operator_crds]
}

# Let's Encrypt ClusterIssuer (Staging - for testing)
# Using kubectl_manifest to avoid planning issues when cluster doesn't exist
resource "kubectl_manifest" "letsencrypt_staging" {
  yaml_body = <<-YAML
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-staging
    spec:
      acme:
        server: https://acme-staging-v02.api.letsencrypt.org/directory
        email: ${var.letsencrypt_email}
        privateKeySecretRef:
          name: letsencrypt-staging-key
        solvers:
          - http01:
              ingress:
                class: nginx
  YAML

  depends_on = [helm_release.cert_manager]
}

# Let's Encrypt ClusterIssuer (Production)
resource "kubectl_manifest" "letsencrypt_prod" {
  yaml_body = <<-YAML
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-prod
    spec:
      acme:
        server: https://acme-v02.api.letsencrypt.org/directory
        email: ${var.letsencrypt_email}
        privateKeySecretRef:
          name: letsencrypt-prod-key
        solvers:
          - http01:
              ingress:
                class: nginx
  YAML

  depends_on = [helm_release.cert_manager]
}

# =============================================================================
# EXTERNAL-DNS (Automatic DNS Record Creation)
# =============================================================================

resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns"
  chart      = "external-dns"
  version    = "1.15.0"
  namespace  = kubernetes_namespace.external_dns.metadata[0].name

  values = [
    yamlencode({
      provider = "azure"

      azure = {
        resourceGroup               = var.resource_group_name
        subscriptionId              = var.subscription_id
        tenantId                    = var.tenant_id
        useManagedIdentityExtension = true
      }

      domainFilters = [var.domain_name]

      policy = "sync" # sync = create and delete records

      sources = ["ingress", "service"]

      txtOwnerId = "${var.environment}-elevaite"

      serviceAccount = {
        create = true
      }
    })
  ]

  depends_on = [kubernetes_namespace.external_dns]
}

# =============================================================================
# QDRANT (Vector Database)
# =============================================================================

resource "kubernetes_namespace" "qdrant" {
  metadata {
    name = "qdrant"
  }
}

resource "helm_release" "qdrant" {
  name       = "qdrant"
  repository = "https://qdrant.github.io/qdrant-helm"
  chart      = "qdrant"
  version    = "0.10.1"
  namespace  = kubernetes_namespace.qdrant.metadata[0].name

  values = [
    yamlencode({
      replicaCount = var.environment == "production" ? 2 : 1

      persistence = {
        size = var.environment == "production" ? "20Gi" : "10Gi"
      }

      resources = {
        requests = {
          cpu    = "250m"
          memory = "512Mi"
        }
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }

      service = {
        type = "ClusterIP"
      }

      apiKey = true
      config = {
        service = {
          api_key = var.qdrant_api_key
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.qdrant, helm_release.prometheus_operator_crds]
}

# =============================================================================
# RABBITMQ (Message Queue)
# =============================================================================

resource "kubernetes_namespace" "rabbitmq" {
  metadata {
    name = "rabbitmq"
  }
}

resource "helm_release" "rabbitmq" {
  name       = "rabbitmq"
  repository = "oci://registry-1.docker.io/bitnamicharts"
  chart      = "rabbitmq"
  version    = "16.0.14"
  namespace  = kubernetes_namespace.rabbitmq.metadata[0].name

  values = [
    yamlencode({
      global = {
        security = {
          allowInsecureImages = true
        }
      }

      image = {
        registry   = "public.ecr.aws"
        repository = "bitnami/rabbitmq"
        tag        = "4.1.3"
      }

      auth = {
        username     = "elevaite"
        password     = var.rabbitmq_password
        erlangCookie = var.rabbitmq_erlang_cookie
      }

      replicaCount = var.environment == "production" ? 3 : 1

      persistence = {
        size = var.environment == "production" ? "16Gi" : "8Gi"
      }

      resources = {
        requests = {
          cpu    = "250m"
          memory = "256Mi"
        }
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }

      service = {
        type = "ClusterIP"
      }

      metrics = {
        enabled = true
        serviceMonitor = {
          enabled = true
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.rabbitmq, helm_release.prometheus_operator_crds]
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

output "qdrant_host" {
  description = "Qdrant service host"
  value       = "qdrant.${kubernetes_namespace.qdrant.metadata[0].name}.svc.cluster.local"
}

output "qdrant_port" {
  description = "Qdrant service port"
  value       = 6333
}

output "rabbitmq_host" {
  description = "RabbitMQ service host"
  value       = "rabbitmq.${kubernetes_namespace.rabbitmq.metadata[0].name}.svc.cluster.local"
}

output "rabbitmq_port" {
  description = "RabbitMQ service port"
  value       = 5672
}
