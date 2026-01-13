#!/bin/bash
set -euo pipefail

echo "========================================="
echo "Kafka Pipeline Cleanup Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop Kubernetes services
print_info "Stopping Kubernetes services..."

if command -v kubectl &> /dev/null; then
    # Delete all deployments in kafka-pipeline namespace
    if kubectl get namespace kafka-pipeline &>/dev/null; then
        print_info "Deleting deployments in kafka-pipeline namespace..."
        kubectl delete deployment --all -n kafka-pipeline --ignore-not-found=true || true
        kubectl delete statefulset --all -n kafka-pipeline --ignore-not-found=true || true
        kubectl delete service --all -n kafka-pipeline --ignore-not-found=true || true
        kubectl delete configmap --all -n kafka-pipeline --ignore-not-found=true || true
        kubectl delete secret --all -n kafka-pipeline --ignore-not-found=true || true
        print_info "Kubernetes resources deleted"
    else
        print_warn "kafka-pipeline namespace does not exist"
    fi
else
    print_warn "kubectl not found, skipping Kubernetes cleanup"
fi

# Stop and remove Docker containers
print_info "Stopping Docker containers..."

if command -v docker &> /dev/null; then
    # Stop all running containers
    print_info "Stopping all running containers..."
    docker stop $(docker ps -q) 2>/dev/null || print_warn "No running containers to stop"
    
    # Remove all stopped containers
    print_info "Removing stopped containers..."
    docker container prune -f || true
    
    # Remove unused images
    print_info "Removing unused Docker images..."
    docker image prune -a -f || true
    
    # Remove unused volumes
    print_info "Removing unused Docker volumes..."
    docker volume prune -f || true
    
    # Remove unused networks
    print_info "Removing unused Docker networks..."
    docker network prune -f || true
    
    # System prune (removes all unused data)
    print_info "Performing Docker system prune..."
    docker system prune -a -f --volumes || true
    
    print_info "Docker cleanup completed"
else
    print_warn "Docker not found, skipping Docker cleanup"
fi

# Remove project-specific files
print_info "Cleaning up project files..."

# Remove node_modules
if [ -d "frontend/node_modules" ]; then
    print_info "Removing frontend/node_modules..."
    rm -rf frontend/node_modules
fi

# Remove venv directories
find . -type d -name "venv" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove .pytest_cache
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files and __pycache__ directories
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove Istio files (if any exist in k8s/istio)
if [ -d "k8s/istio" ]; then
    print_info "Cleaning Istio directory..."
    rm -rf k8s/istio/* 2>/dev/null || true
fi

print_info "Project files cleaned up"

echo ""
print_info "========================================="
print_info "Cleanup completed successfully!"
print_info "========================================="
