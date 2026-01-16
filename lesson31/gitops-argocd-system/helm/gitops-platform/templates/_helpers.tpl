{{- define "gitops-platform.fullname" -}}
{{- .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "gitops-platform.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "gitops-platform.labels" -}}
app.kubernetes.io/name: {{ include "gitops-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "gitops-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "gitops-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
