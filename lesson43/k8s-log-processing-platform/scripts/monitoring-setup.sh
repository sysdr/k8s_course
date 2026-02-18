#!/bin/bash
set -euo pipefail

echo "📊 Setting up monitoring stack..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
echo "🔍 Deploying Prometheus..."
kubectl apply -f ../monitoring/prometheus/

# Deploy Grafana
echo "📈 Deploying Grafana..."
cat <<GRAFANAEOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: grafana
GRAFANAEOF

# Deploy Jaeger
echo "🔎 Deploying Jaeger..."
kubectl apply -f ../monitoring/jaeger/

echo "✅ Monitoring stack deployed!"
echo ""
echo "Access Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "Access Jaeger: kubectl port-forward -n monitoring svc/jaeger 16686:16686"
