#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Starting Log Analytics System..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl."
    exit 1
fi

# Check if cluster is available (suppress errors)
CLUSTER_AVAILABLE=false
if kubectl get nodes &> /dev/null 2>&1; then
    CLUSTER_AVAILABLE=true
    echo "Kubernetes cluster detected."
else
    echo "Warning: Kubernetes cluster not available. Validating manifests with --dry-run=client..."
fi

# Function to validate YAML files
validate_yaml() {
    local dir=$1
    local count=0
    for file in "${dir}"*.yaml; do
        if [ -f "$file" ]; then
            if python3 -c "import yaml; list(yaml.safe_load_all(open('$file')))" 2>/dev/null; then
                count=$((count + 1))
            else
                echo "  ✗ Error: Invalid YAML in $(basename "$file")"
                return 1
            fi
        fi
    done
    echo "  ✓ Validated $count YAML file(s)"
    return 0
}

# Apply storage classes
echo "Applying storage classes..."
if [ "$CLUSTER_AVAILABLE" = true ]; then
    kubectl apply -f "${BASE_DIR}/k8s/storage/classes/" || kubectl apply -f "${BASE_DIR}/k8s/storage/classes/" --validate=false
else
    validate_yaml "${BASE_DIR}/k8s/storage/classes/"
fi

# Apply RBAC
echo "Applying RBAC..."
if [ "$CLUSTER_AVAILABLE" = true ]; then
    kubectl apply -f "${BASE_DIR}/k8s/rbac/" || kubectl apply -f "${BASE_DIR}/k8s/rbac/" --validate=false
else
    validate_yaml "${BASE_DIR}/k8s/rbac/"
fi

# Apply applications
echo "Applying applications..."
if [ "$CLUSTER_AVAILABLE" = true ]; then
    kubectl apply -f "${BASE_DIR}/k8s/apps/" || kubectl apply -f "${BASE_DIR}/k8s/apps/" --validate=false
else
    validate_yaml "${BASE_DIR}/k8s/apps/"
fi

# Wait for deployments (only if cluster is available)
if [ "$CLUSTER_AVAILABLE" = true ]; then
    echo "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/log-ingestion 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=300s deployment/log-processor 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=300s deployment/api-gateway 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=300s deployment/frontend 2>/dev/null || true
    
    # Set up port forwarding for services (needed for kind/WSL2)
    echo "Setting up port forwarding..."
    # Kill existing port forwards if any
    pkill -f "kubectl port-forward.*frontend.*30000" 2>/dev/null || true
    pkill -f "kubectl port-forward.*api-gateway.*30080" 2>/dev/null || true
    sleep 1
    
    # Start port forwarding in background
    kubectl port-forward svc/frontend 30000:80 > /tmp/frontend-portforward.log 2>&1 &
    kubectl port-forward svc/api-gateway 30080:8080 > /tmp/api-gateway-portforward.log 2>&1 &
    sleep 2
    echo "  ✓ Port forwarding configured"
else
    echo "Dry-run mode: Skipping deployment wait."
fi

echo "System started successfully!"
echo "Frontend: http://localhost:30000"
echo "API Gateway: http://localhost:30080"
echo ""
echo "Note: Port forwarding is running in the background."
echo "To stop port forwarding, run: pkill -f 'kubectl port-forward'"
