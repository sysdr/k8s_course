#!/bin/bash
set -euo pipefail

echo "Deploying Log Analytics Platform with NGINX Ingress..."

cd "$(dirname "$0")/.."

# Deploy NGINX Ingress Controller
echo "1. Deploying NGINX Ingress Controller..."
kubectl apply -f k8s/ingress-controller/namespace.yaml
kubectl apply -f k8s/ingress-controller/configmap.yaml
kubectl apply -f k8s/ingress-controller/serviceaccount.yaml
kubectl apply -f k8s/ingress-controller/ingressclass.yaml
kubectl apply -f k8s/ingress-controller/deployment.yaml
kubectl apply -f k8s/ingress-controller/service.yaml

echo "Waiting for Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s || true

# Deploy monitoring namespace and resources
echo "2. Deploying monitoring stack..."
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml

# Deploy application services
echo "3. Deploying application services..."
kubectl apply -f k8s/services/log-ingestion-deployment.yaml
kubectl apply -f k8s/services/query-service-deployment.yaml
kubectl apply -f k8s/services/analytics-service-deployment.yaml
kubectl apply -f k8s/services/frontend-deployment.yaml

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/log-ingestion \
  deployment/query-service \
  deployment/analytics-service \
  deployment/frontend || true

# Deploy Ingress resources
echo "4. Deploying Ingress resources..."
kubectl apply -f k8s/ingress/main-ingress.yaml
kubectl apply -f k8s/ingress/rate-limited-ingress.yaml

# Display status
echo ""
echo "========================================="
echo "Deployment Status"
echo "========================================="
echo ""

echo "NGINX Ingress Controller:"
kubectl get pods -n ingress-nginx
echo ""

echo "Application Pods:"
kubectl get pods
echo ""

echo "Services:"
kubectl get svc
echo ""

echo "Ingress Resources:"
kubectl get ingress
echo ""

echo "========================================="
echo "Access Information"
echo "========================================="
echo ""

# Get Ingress external IP/port
INGRESS_IP=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
INGRESS_PORT=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}' 2>/dev/null || echo "80")

if [ "$INGRESS_IP" == "pending" ] || [ -z "$INGRESS_IP" ]; then
    echo "⚠️  LoadBalancer IP is pending. For local clusters, use:"
    echo "   kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80"
    echo "   Then access: http://localhost:8080"
else
    echo "✓ Application URL: http://$INGRESS_IP"
fi

echo ""
echo "API Endpoints:"
echo "  - Log Ingestion: http://localhost:8080/api/ingest"
echo "  - Query API: http://localhost:8080/api/query"
echo "  - Analytics API: http://localhost:8080/api/analytics"
echo ""
echo "Monitoring:"
echo "  kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "  kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo ""
echo "✓ Deployment complete!"
