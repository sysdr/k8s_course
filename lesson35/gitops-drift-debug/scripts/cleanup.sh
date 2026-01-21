#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "GitOps Drift Detection System - Cleanup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Stop Kubernetes services
print_info "Stopping Kubernetes services..."
if kubectl cluster-info &>/dev/null; then
    # Delete all applications
    print_info "Deleting applications..."
    kubectl delete applications -n argocd --all --ignore-not-found=true 2>/dev/null || true
    
    # Delete deployments
    print_info "Deleting deployments..."
    kubectl delete deployments -n production --all --ignore-not-found=true 2>/dev/null || true
    kubectl delete deployments -n monitoring --all --ignore-not-found=true 2>/dev/null || true
    
    # Delete services
    print_info "Deleting services..."
    kubectl delete svc -n production --all --ignore-not-found=true 2>/dev/null || true
    kubectl delete svc -n monitoring --all --ignore-not-found=true 2>/dev/null || true
    
    # Delete kind cluster
    print_info "Deleting kind cluster..."
    if kind get clusters | grep -q "gitops-drift"; then
        kind delete cluster --name gitops-drift 2>/dev/null || true
        print_info "Kind cluster deleted"
    else
        print_warning "Kind cluster 'gitops-drift' not found"
    fi
else
    print_warning "Kubernetes cluster not accessible, skipping..."
fi

# 2. Stop Docker containers
print_info "Stopping Docker containers..."
docker ps -q | xargs -r docker stop 2>/dev/null || true
print_info "All running containers stopped"

# 3. Remove stopped containers
print_info "Removing stopped containers..."
docker container prune -f 2>/dev/null || true

# 4. Remove unused Docker images
print_info "Removing unused Docker images..."
docker image prune -a -f 2>/dev/null || true

# 5. Remove unused Docker volumes
print_info "Removing unused Docker volumes..."
docker volume prune -f 2>/dev/null || true

# 6. Remove unused Docker networks
print_info "Removing unused Docker networks..."
docker network prune -f 2>/dev/null || true

# 7. Clean up build cache
print_info "Removing Docker build cache..."
docker builder prune -a -f 2>/dev/null || true

# 8. Remove Python cache files
print_info "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
print_info "Python cache files removed"

# 9. Remove node_modules
print_info "Removing node_modules..."
find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
print_info "node_modules removed"

# 10. Remove virtual environments
print_info "Removing virtual environments..."
find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "env" -exec rm -rf {} + 2>/dev/null || true
print_info "Virtual environments removed"

# 11. Remove Istio files
print_info "Removing Istio files..."
find . -path "*/istio/*" -type f -delete 2>/dev/null || true
find . -type d -name "istio" -empty -delete 2>/dev/null || true
print_info "Istio files removed"

# 12. Remove temporary files
print_info "Removing temporary files..."
find . -name "*.log" -type f -delete 2>/dev/null || true
find . -name "*.tmp" -type f -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
print_info "Temporary files removed"

# 13. Show Docker system info
echo ""
print_info "Docker system summary:"
docker system df 2>/dev/null || true

echo ""
print_info "=========================================="
print_info "Cleanup completed successfully!"
print_info "=========================================="
echo ""
