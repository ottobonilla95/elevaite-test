{{/*
Expand the name of the chart.
*/}}
{{- define "elevaite.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "elevaite.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "elevaite.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "elevaite.labels" -}}
helm.sh/chart: {{ include "elevaite.chart" . }}
{{ include "elevaite.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.labels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "elevaite.selectorLabels" -}}
app.kubernetes.io/name: {{ include "elevaite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "elevaite.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "elevaite.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "elevaite.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Full image name with registry
*/}}
{{- define "elevaite.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- $repository := .image.repository -}}
{{- $tag := .image.tag | default "latest" -}}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
PostgreSQL connection URL (External Managed Database Only)
Credentials come from existingSecret, this just builds the host/port/db part
*/}}
{{- define "elevaite.postgresqlUrl" -}}
{{- $host := required "postgresql.host is required" .Values.postgresql.host -}}
{{- $port := .Values.postgresql.port | default 5432 -}}
{{- $database := .Values.postgresql.database | default "elevaite" -}}
{{- $sslMode := .Values.postgresql.sslMode | default "require" -}}
{{- printf "postgresql://%s:%d/%s?sslmode=%s" $host (int $port) $database $sslMode }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "elevaite.postgresqlHost" -}}
{{- required "postgresql.host is required" .Values.postgresql.host -}}
{{- end }}

{{/*
RabbitMQ connection URL
Uses internal service if internal.enabled, otherwise external managed service
*/}}
{{- define "elevaite.rabbitmqUrl" -}}
{{- if .Values.rabbitmq.internal.enabled -}}
{{- $host := printf "%s-rabbitmq" (include "elevaite.fullname" .) -}}
{{- $port := 5672 -}}
{{- $vhost := "/" -}}
{{- printf "amqp://%s:%d%s" $host (int $port) $vhost }}
{{- else -}}
{{- $host := required "rabbitmq.host is required when rabbitmq.internal.enabled is false" .Values.rabbitmq.host -}}
{{- $port := .Values.rabbitmq.port | default 5672 -}}
{{- $vhost := .Values.rabbitmq.vhost | default "/" -}}
{{- printf "amqp://%s:%d%s" $host (int $port) $vhost }}
{{- end -}}
{{- end }}

{{/*
RabbitMQ host
*/}}
{{- define "elevaite.rabbitmqHost" -}}
{{- if .Values.rabbitmq.internal.enabled -}}
{{- printf "%s-rabbitmq" (include "elevaite.fullname" .) -}}
{{- else -}}
{{- required "rabbitmq.host is required when rabbitmq.internal.enabled is false" .Values.rabbitmq.host -}}
{{- end -}}
{{- end }}

{{/*
Object Storage endpoint (S3/GCS/Azure Blob)
*/}}
{{- define "elevaite.storageEndpoint" -}}
{{- if eq .Values.objectStorage.provider "aws" -}}
{{- if .Values.objectStorage.endpoint -}}
{{- .Values.objectStorage.endpoint -}}
{{- else -}}
{{- printf "https://s3.%s.amazonaws.com" .Values.objectStorage.region -}}
{{- end -}}
{{- else if eq .Values.objectStorage.provider "gcp" -}}
{{- "https://storage.googleapis.com" -}}
{{- else if eq .Values.objectStorage.provider "azure" -}}
{{- .Values.objectStorage.endpoint -}}
{{- else -}}
{{- .Values.objectStorage.endpoint | default "http://localhost:9000" -}}
{{- end -}}
{{- end }}

{{/*
Object Storage bucket name
*/}}
{{- define "elevaite.storageBucket" -}}
{{- required "objectStorage.bucket is required" .Values.objectStorage.bucket -}}
{{- end }}

{{/*
Environment name from global config
*/}}
{{- define "elevaite.environment" -}}
{{- .Values.global.environment | default "dev" -}}
{{- end }}
