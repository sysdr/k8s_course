#!/bin/bash

set -euo pipefail

echo "🚀 Deploying debugging challenge system..."

cd "$(dirname "$0")/.."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Create namespace
kubectl create namespace debugging-challenge --dry-run=client -o yaml | kubectl apply -f -

# Label namespace for Istio injection
# Try modern label first, fallback to legacy if needed
if kubectl get namespace istio-system &>/dev/null; then
    # Istio is installed, use revision-based injection
    kubectl label namespace debugging-challenge istio.io/rev=default --overwrite
    kubectl label namespace debugging-challenge istio-injection- 2>/dev/null || true
else
    # Legacy label for older Istio versions
    kubectl label namespace debugging-challenge istio-injection=enabled --overwrite
fi

# Apply base Kubernetes resources
echo "Applying base resources..."
kubectl apply -f k8s/base/ -n debugging-challenge

# Apply NetworkPolicies
echo "Applying NetworkPolicies (with bugs)..."
kubectl apply -f k8s/networkpolicy/ -n debugging-challenge

# Apply Ingress
echo "Applying Ingress (with bugs)..."
kubectl apply -f k8s/ingress/ -n debugging-challenge

# Apply Istio configurations
echo "Applying Istio configs (with bugs)..."
kubectl apply -f k8s/istio/ -n debugging-challenge || echo "⚠️  Istio not installed - skipping Istio configs (bugs #4 and #5 require Istio)"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🐛 DEBUGGING CHALLENGE ACTIVE 🐛"
echo "================================"
echo ""
echo "Your mission: Find and fix 5 networking bugs:"
echo "  1. Ingress returning 404"
echo "  2. Service not finding pods"
echo "  3. NetworkPolicy blocking traffic"
echo "  4. Istio routing to non-existent subset"
echo "  5. Service mesh configuration mismatch"
echo ""
echo "Start debugging with:"
echo "  kubectl get pods -n debugging-challenge"
echo "  kubectl get svc -n debugging-challenge"
echo "  kubectl get ingress -n debugging-challenge"
echo ""
echo "Good luck! 🔍"
