#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🚀 Starting E-Commerce System..."
echo "================================"

cd "${PROJECT_ROOT}"

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ docker not found. Please install docker first."
    exit 1
fi

# Build images
echo ""
echo "🔨 Building container images..."
"${SCRIPT_DIR}/build.sh"

# Load images into kind cluster if using kind
if command -v kind &> /dev/null; then
    CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
    if [[ "${CURRENT_CONTEXT}" == kind-* ]]; then
        CLUSTER_NAME="${CURRENT_CONTEXT#kind-}"
        echo ""
        echo "📦 Loading images into kind cluster '${CLUSTER_NAME}'..."
        kind load docker-image ecommerce-frontend:latest --name "${CLUSTER_NAME}" || true
        kind load docker-image ecommerce-backend:latest --name "${CLUSTER_NAME}" || true
        kind load docker-image dashboard:latest --name "${CLUSTER_NAME}" || true
    fi
fi

# Deploy to Kubernetes
echo ""
echo "📦 Deploying to Kubernetes..."
"${SCRIPT_DIR}/deploy.sh"

# Wait for pods to be ready
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --all -n debugging-challenge --timeout=300s || true

# Deploy monitoring
echo ""
echo "📊 Deploying monitoring stack..."
kubectl apply -f "${PROJECT_ROOT}/monitoring/" -n debugging-challenge || true

# Wait for monitoring to be ready
echo ""
echo "⏳ Waiting for monitoring to be ready..."
sleep 10

# Show status
echo ""
echo "✅ Startup complete!"
echo ""
echo "📊 System Status:"
kubectl get pods -n debugging-challenge
echo ""
echo "🔌 Services:"
kubectl get svc -n debugging-challenge
echo ""
echo "🌐 Ingress:"
kubectl get ingress -n debugging-challenge
echo ""
echo "📈 Monitoring:"
kubectl get pods -n debugging-challenge | grep -E "(prometheus|grafana)" || echo "  Monitoring pods not found"
echo ""
echo "🚀 Next steps:"
echo "  ./scripts/demo.sh          # Run demo to generate metrics"
echo "  ./scripts/test.sh          # Run tests"
echo "  ./scripts/debug-helper.sh  # Debug helper"
echo ""
echo "📊 Dashboard:"
echo "  kubectl port-forward -n debugging-challenge svc/dashboard-service 5000:5000"
echo "  Then open http://localhost:5000 in your browser"
