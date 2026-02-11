#!/bin/bash
set -euo pipefail
# deploy.sh — full orchestration: apply K8s manifests + Istio + monitoring.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/.."

echo "=== Applying namespaces …"
kubectl apply -f "${ROOT}/k8s/namespaces/"

echo "=== Applying RBAC …"
kubectl apply -f "${ROOT}/k8s/rbac/"

echo "=== Applying ConfigMaps & Secrets …"
kubectl apply -f "${ROOT}/k8s/configmaps/"
kubectl apply -f "${ROOT}/k8s/secrets/"

echo "=== Applying Deployments …"
kubectl apply -f "${ROOT}/k8s/deployments/"

echo "=== Applying Services …"
kubectl apply -f "${ROOT}/k8s/services/"

echo "=== Applying Autoscaling (HPA/VPA) …"
kubectl apply -f "${ROOT}/k8s/autoscaling/" 2>/dev/null || echo "NOTE: VPA CRDs may not be installed — VPA manifests skipped."

echo "=== Applying PodDisruptionBudgets …"
kubectl apply -f "${ROOT}/k8s/pdb/"

echo "=== Applying NetworkPolicies …"
kubectl apply -f "${ROOT}/k8s/networking/"

echo "=== Applying Ingress …"
kubectl apply -f "${ROOT}/k8s/ingress/"

echo "=== Applying Istio resources …"
kubectl apply -f "${ROOT}/istio/"

echo "=== Deploying monitoring stack …"
bash "${SCRIPT_DIR}/monitoring-setup.sh"

echo ""
echo "=== All resources applied."
echo "  Check status:  kubectl get pods -n app -w"
echo "  Port-forward:  kubectl port-forward svc/frontend 8080:80 -n app"
