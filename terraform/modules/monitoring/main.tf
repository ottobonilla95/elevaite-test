# =============================================================================
# Monitoring Stack Module
# Deploys: Prometheus, Grafana, Loki, Alertmanager
# Cloud-agnostic observability stack
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
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

variable "environment" {
  description = "Environment name: dev, staging, or production"
  type        = string
}

variable "domain_name" {
  description = "Domain name for Grafana ingress (e.g., elevaite.ai)"
  type        = string
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
  description = "PagerDuty service integration key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "storage_class" {
  description = "Storage class for persistent volumes"
  type        = string
  default     = ""
}

variable "retention_days" {
  description = "Prometheus metrics retention in days"
  type        = number
  default     = 15
}

# Additional variables expected by environment configurations
variable "prometheus_retention_days" {
  description = "Prometheus metrics retention in days (alias for retention_days)"
  type        = number
  default     = null
}

variable "prometheus_storage_size" {
  description = "Prometheus storage size"
  type        = string
  default     = ""
}

variable "loki_retention_days" {
  description = "Loki logs retention in days"
  type        = number
  default     = null
}

variable "loki_storage_size" {
  description = "Loki storage size"
  type        = string
  default     = ""
}

variable "grafana_domain" {
  description = "Grafana domain (alias for domain_name)"
  type        = string
  default     = ""
}

variable "alertmanager_enabled" {
  description = "Enable Alertmanager"
  type        = bool
  default     = true
}

variable "project_name" {
  description = "Project name for labeling"
  type        = string
  default     = "elevaite"
}

locals {
  # Use prometheus_retention_days if set, otherwise fall back to retention_days
  effective_retention_days = coalesce(var.prometheus_retention_days, var.retention_days)
  # Use grafana_domain if set, otherwise fall back to domain_name
  effective_domain = var.grafana_domain != "" ? var.grafana_domain : var.domain_name
  # Loki retention defaults to same as prometheus if not set
  effective_loki_retention = coalesce(var.loki_retention_days, var.retention_days)
}

# =============================================================================
# NAMESPACE
# =============================================================================

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# =============================================================================
# PROMETHEUS STACK (Prometheus, Grafana, Alertmanager)
# =============================================================================

resource "helm_release" "prometheus_stack" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "55.5.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    yamlencode({
      # Prometheus
      prometheus = {
        prometheusSpec = {
          retention = "${local.effective_retention_days}d"
          
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class != "" ? var.storage_class : null
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.environment == "production" ? "100Gi" : "20Gi"
                  }
                }
              }
            }
          }

          resources = {
            requests = {
              cpu    = var.environment == "production" ? "500m" : "250m"
              memory = var.environment == "production" ? "2Gi" : "1Gi"
            }
            limits = {
              cpu    = var.environment == "production" ? "2000m" : "500m"
              memory = var.environment == "production" ? "4Gi" : "2Gi"
            }
          }

          # Service discovery
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues     = false
        }
      }

      # Alertmanager
      alertmanager = {
        alertmanagerSpec = {
          storage = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class != "" ? var.storage_class : null
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "10Gi"
                  }
                }
              }
            }
          }
        }

        config = {
          global = {
            resolve_timeout = "5m"
          }
          route = {
            group_by        = ["alertname", "namespace"]
            group_wait      = "30s"
            group_interval  = "5m"
            repeat_interval = "4h"
            receiver        = "default"
            routes = var.environment == "production" ? [
              {
                match = {
                  severity = "critical"
                }
                receiver = "pagerduty"
              },
              {
                match = {
                  severity = "warning"
                }
                receiver = "slack"
              }
            ] : []
          }
          receivers = concat(
            [{
              name = "default"
            }],
            var.slack_webhook_url != "" ? [{
              name = "slack"
              slack_configs = [{
                api_url = var.slack_webhook_url
                channel = "#alerts-${var.environment}"
                title   = "{{ .GroupLabels.alertname }}"
                text    = "{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}"
              }]
            }] : [],
            var.pagerduty_service_key != "" ? [{
              name = "pagerduty"
              pagerduty_configs = [{
                service_key = var.pagerduty_service_key
              }]
            }] : []
          )
        }
      }

      # Grafana
      grafana = {
        enabled = true

        adminPassword = var.grafana_admin_password

        ingress = {
          enabled = true
          annotations = {
            "kubernetes.io/ingress.class"                    = "nginx"
            "cert-manager.io/cluster-issuer"                 = var.environment == "production" ? "letsencrypt-prod" : "letsencrypt-staging"
            "nginx.ingress.kubernetes.io/ssl-redirect"       = "true"
          }
          hosts = [local.effective_domain]
          tls = [{
            secretName = "grafana-tls"
            hosts      = [local.effective_domain]
          }]
        }

        persistence = {
          enabled          = true
          storageClassName = var.storage_class != "" ? var.storage_class : null
          size             = "10Gi"
        }

        # Default dashboards
        dashboardProviders = {
          "dashboardproviders.yaml" = {
            apiVersion = 1
            providers = [{
              name            = "default"
              orgId           = 1
              folder          = ""
              type            = "file"
              disableDeletion = false
              editable        = true
              options = {
                path = "/var/lib/grafana/dashboards/default"
              }
            }]
          }
        }

        # Pre-configured dashboards
        dashboards = {
          default = {
            kubernetes-cluster = {
              gnetId     = 7249
              revision   = 1
              datasource = "Prometheus"
            }
            nginx-ingress = {
              gnetId     = 9614
              revision   = 1
              datasource = "Prometheus"
            }
          }
        }

        # Data sources
        additionalDataSources = [{
          name      = "Loki"
          type      = "loki"
          url       = "http://loki:3100"
          access    = "proxy"
          isDefault = false
        }]
      }

      # Node exporter
      nodeExporter = {
        enabled = true
      }

      # Kube state metrics
      kubeStateMetrics = {
        enabled = true
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# =============================================================================
# LOKI (Log Aggregation)
# =============================================================================

resource "helm_release" "loki" {
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = "5.41.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    yamlencode({
      loki = {
        auth_enabled = false

        storage = {
          type = "filesystem"
        }

        commonConfig = {
          replication_factor = 1
        }

        limits_config = {
          retention_period = "${local.effective_loki_retention * 24}h"
        }
      }

      singleBinary = {
        replicas = 1
        persistence = {
          enabled          = true
          storageClassName = var.storage_class != "" ? var.storage_class : null
          size             = var.environment == "production" ? "50Gi" : "10Gi"
        }
      }

      monitoring = {
        selfMonitoring = {
          enabled = false
        }
        lokiCanary = {
          enabled = false
        }
      }

      test = {
        enabled = false
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# =============================================================================
# PROMTAIL (Log Shipping to Loki)
# =============================================================================

resource "helm_release" "promtail" {
  name       = "promtail"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "promtail"
  version    = "6.15.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    yamlencode({
      config = {
        clients = [{
          url = "http://loki:3100/loki/api/v1/push"
        }]
      }
    })
  ]

  depends_on = [helm_release.loki]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "grafana_url" {
  description = "Grafana URL"
  value       = "https://${local.effective_domain}"
}

output "prometheus_url" {
  description = "Prometheus internal URL"
  value       = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
}

output "alertmanager_url" {
  description = "Alertmanager internal URL"
  value       = "http://prometheus-kube-prometheus-alertmanager.monitoring.svc.cluster.local:9093"
}

output "loki_url" {
  description = "Loki internal URL"
  value       = "http://loki.monitoring.svc.cluster.local:3100"
}
