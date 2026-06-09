{{/*
Expand the name of the chart.
*/}}
{{- define "vagrantfile-generator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "vagrantfile-generator.fullname" -}}
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
Chart target namespace.
*/}}
{{- define "vagrantfile-generator.namespace" -}}
{{- default .Release.Namespace .Values.namespace.name -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "vagrantfile-generator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "vagrantfile-generator.labels" -}}
helm.sh/chart: {{ include "vagrantfile-generator.chart" . }}
{{ include "vagrantfile-generator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "vagrantfile-generator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "vagrantfile-generator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend name
*/}}
{{- define "vagrantfile-generator.backend.name" -}}
{{- printf "%s-backend" (include "vagrantfile-generator.fullname" .) }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "vagrantfile-generator.backend.labels" -}}
{{ include "vagrantfile-generator.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "vagrantfile-generator.backend.selectorLabels" -}}
{{ include "vagrantfile-generator.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend name
*/}}
{{- define "vagrantfile-generator.frontend.name" -}}
{{- printf "%s-frontend" (include "vagrantfile-generator.fullname" .) }}
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "vagrantfile-generator.frontend.labels" -}}
{{ include "vagrantfile-generator.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "vagrantfile-generator.frontend.selectorLabels" -}}
{{ include "vagrantfile-generator.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Secret name
*/}}
{{- define "vagrantfile-generator.secretName" -}}
{{- printf "%s-secret" (include "vagrantfile-generator.fullname" .) }}
{{- end }}

{{/*
Frontend ConfigMap name
*/}}
{{- define "vagrantfile-generator.frontend.configMapName" -}}
{{- printf "%s-nginx-config" (include "vagrantfile-generator.frontend.name" .) }}
{{- end }}

{{/*
Backend service URL (internal)
*/}}
{{- define "vagrantfile-generator.backend.serviceUrl" -}}
{{- printf "http://%s:%d" (include "vagrantfile-generator.backend.name" .) (int .Values.backend.port) }}
{{- end }}

{{/*
Frontend external URL
*/}}
{{- define "vagrantfile-generator.frontend.externalUrl" -}}
{{- printf "https://%s" .Values.gatewayAPI.hostname }}
{{- end }}

{{/*
Backend external URL (via Gateway API)
*/}}
{{- define "vagrantfile-generator.backend.externalUrl" -}}
{{- printf "https://%s" .Values.gatewayAPI.hostname }}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "vagrantfile-generator.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}

{{/*
TLS secret name
*/}}
{{- define "vagrantfile-generator.tlsSecretName" -}}
{{- printf "%s-tls" (include "vagrantfile-generator.fullname" .) }}
{{- end }}

{{/*
ListenerSet name
*/}}
{{- define "vagrantfile-generator.listenerSet.name" -}}
{{- printf "%s-listeners" (include "vagrantfile-generator.fullname" .) }}
{{- end }}
