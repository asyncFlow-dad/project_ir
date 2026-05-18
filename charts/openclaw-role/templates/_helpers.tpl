{{- define "openclaw-role.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "openclaw-role.fullname" -}}
{{- printf "openclaw-%s" .Values.role -}}
{{- end -}}
