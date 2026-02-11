#!/bin/bash
set -euo pipefail
# monitoring-setup.sh — deploy Prometheus, Grafana, Jaeger, OTel Collector.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/.."
NS="observability"

echo "=== Deploying Jaeger all-in-one …"
kubectl apply -n "${NS}" -f "${ROOT}/monitoring/jaeger/jaeger-all-in-one.yaml"

echo "=== Deploying OTel Collector (DaemonSet) …"
kubectl apply -n "${NS}" -f "${ROOT}/monitoring/jaeger/otel-collector.yaml"

echo "=== Installing kube-prometheus-stack via Helm …"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace "${NS}" --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword=${GRAFANA_PASSWORD:-changeme} \
  --set prometheus.enabled=true

echo "=== Applying ServiceMonitors …"
kubectl apply -n "${NS}" -f "${ROOT}/monitoring/prometheus/service-monitors.yaml"

echo "=== Applying AlertingRules …"
kubectl apply -n "${NS}" -f "${ROOT}/monitoring/prometheus/alerting-rules.yaml"

echo ""
echo "=== Monitoring stack deployed."
echo "  Grafana:  kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n ${NS}"
echo "  Jaeger:   kubectl port-forward svc/jaeger-query 16686:16686 -n ${NS}"
echo "  Prom:     kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n ${NS}"
