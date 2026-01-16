#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "============================================"
echo "GitOps Platform Startup Script"
echo "============================================"
echo ""

# Function to check if a service is running
check_service() {
    local service_name="$1"
    local port="$2"
    
    if command -v lsof &> /dev/null; then
        if lsof -i :"${port}" &> /dev/null; then
            echo "⚠️  ${service_name} is already running on port ${port}"
            return 0
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            echo "⚠️  ${service_name} is already running on port ${port}"
            return 0
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            echo "⚠️  ${service_name} is already running on port ${port}"
            return 0
        fi
    fi
    
    return 1
}

# Check for duplicate services
echo "Checking for running services..."
DUPLICATES_FOUND=0

if check_service "metrics-aggregator" "8000"; then
    DUPLICATES_FOUND=1
fi

if check_service "event-processor" "8001"; then
    DUPLICATES_FOUND=1
fi

if check_service "dashboard" "80"; then
    DUPLICATES_FOUND=1
fi

if check_service "argocd-server" "8080"; then
    DUPLICATES_FOUND=1
fi

if [ $DUPLICATES_FOUND -eq 1 ]; then
    echo ""
    echo "⚠️  Warning: Some services appear to be already running."
    echo "   Please stop them before starting new instances to avoid conflicts."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ""
echo "Starting GitOps Platform..."
echo ""

# Check if cluster exists
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not found or not accessible"
    echo "   Please run: ${SCRIPT_DIR}/setup-cluster.sh"
    exit 1
fi

# Check if ArgoCD is installed
if ! kubectl get namespace argocd &> /dev/null; then
    echo "ArgoCD not found. Installing..."
    bash "${SCRIPT_DIR}/install-argocd.sh"
else
    echo "✓ ArgoCD namespace exists"
fi

# Check if applications are deployed
if ! kubectl get applications -n argocd &> /dev/null || [ -z "$(kubectl get applications -n argocd --no-headers 2>/dev/null)" ]; then
    echo "Deploying applications..."
    bash "${SCRIPT_DIR}/deploy.sh"
else
    echo "✓ ArgoCD applications exist"
fi

# Wait for pods to be ready
echo ""
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=metrics-aggregator -n gitops-apps-prod --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=event-processor -n gitops-apps-prod --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=dashboard -n gitops-apps-prod --timeout=300s 2>/dev/null || true

echo ""
echo "============================================"
echo "✅ Platform started successfully!"
echo "============================================"
echo ""
echo "Access services:"
echo ""
echo "1. ArgoCD UI:"
echo "   kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "   https://localhost:8080 (admin/$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' 2>/dev/null | base64 -d 2>/dev/null || echo 'check argocd-password.txt'))"
echo ""
echo "2. Dashboard:"
echo "   kubectl port-forward svc/dashboard -n gitops-apps-prod 8081:80"
echo "   http://localhost:8081"
echo ""
echo "3. Metrics Aggregator API:"
echo "   kubectl port-forward svc/metrics-aggregator -n gitops-apps-prod 8000:8000"
echo "   http://localhost:8000/api/applications"
echo ""
echo "4. Event Processor API:"
echo "   kubectl port-forward svc/event-processor -n gitops-apps-prod 8001:8001"
echo "   http://localhost:8001/api/stats"
echo ""
echo "============================================"
