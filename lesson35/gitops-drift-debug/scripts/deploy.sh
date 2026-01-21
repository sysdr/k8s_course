#!/bin/bash
set -euo pipefail

echo "Deploying GitOps drift detection system..."

# Deploy infrastructure
echo "Deploying infrastructure..."
kubectl apply -f infrastructure/redis/

# Deploy monitoring
echo "Deploying monitoring stack..."
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/

# Deploy applications via ArgoCD
echo "Deploying applications via ArgoCD..."
kubectl apply -f gitops/applications/

echo ""
echo "Deployment initiated!"
echo "===================="
echo ""
echo "Check ArgoCD for sync status:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "Access services:"
echo "  Frontend: kubectl port-forward svc/frontend -n production 3000:80"
echo "  API: kubectl port-forward svc/api-service -n production 8000:8000"
echo "  Grafana: kubectl port-forward svc/grafana -n monitoring 3001:3000"
echo "  Prometheus: kubectl port-forward svc/prometheus -n monitoring 9090:9090"
echo ""
