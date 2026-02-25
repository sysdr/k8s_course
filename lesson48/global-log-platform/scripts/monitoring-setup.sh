#!/bin/bash
# monitoring-setup.sh — Deploy Prometheus + Grafana + Jaeger via Helm
set -euo pipefail
CONTEXT="${1:-kind-us-east}"

kubectl --context "${CONTEXT}" create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Prometheus stack
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --kube-context "${CONTEXT}" \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=15d \
  --set grafana.adminPassword=admin123 \
  --wait

# Jaeger
helm upgrade --install jaeger jaegertracing/jaeger \
  --kube-context "${CONTEXT}" \
  --namespace monitoring \
  --set provisionDataStore.cassandra=false \
  --set allInOne.enabled=true \
  --wait

echo "✓ Monitoring stack deployed on ${CONTEXT}"
echo "Grafana: kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
echo "Jaeger:  kubectl port-forward -n monitoring svc/jaeger-query 16686:16686"
