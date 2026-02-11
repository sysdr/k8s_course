#!/bin/bash
# Comprehensive cleanup script for Kubernetes Alerting System
# Stops all services, removes Docker resources, and cleans up project files

set -e

echo "=========================================="
echo "Kubernetes Alerting System Cleanup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Stop port-forwards
echo "1. Stopping port-forwards..."
pkill -f "kubectl port-forward" 2>/dev/null && print_status "Port-forwards stopped" || print_warning "No port-forwards running"

# 2. Stop Kubernetes services
echo ""
echo "2. Stopping Kubernetes services..."
if kubectl cluster-info >/dev/null 2>&1; then
    # Stop services in namespaces
    kubectl delete --all deployments,statefulsets,services,configmaps -n log-processing 2>/dev/null || true
    kubectl delete --all deployments,statefulsets,services,configmaps -n monitoring 2>/dev/null || true
    print_status "Kubernetes services stopped"
else
    print_warning "Kubernetes cluster not accessible"
fi

# 3. Stop Docker containers
echo ""
echo "3. Stopping Docker containers..."
RUNNING_CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
    docker stop $(docker ps -q) 2>/dev/null && print_status "Stopped $RUNNING_CONTAINERS running containers" || print_warning "Some containers may not have stopped"
else
    print_status "No running containers"
fi

# 4. Remove stopped containers
echo ""
echo "4. Removing stopped containers..."
STOPPED_CONTAINERS=$(docker ps -aq 2>/dev/null | wc -l)
if [ "$STOPPED_CONTAINERS" -gt 0 ]; then
    docker rm $(docker ps -aq) 2>/dev/null && print_status "Removed $STOPPED_CONTAINERS stopped containers" || print_warning "Some containers may not have been removed"
else
    print_status "No stopped containers"
fi

# 5. Remove unused Docker images
echo ""
echo "5. Removing unused Docker images..."
docker image prune -af --filter "dangling=true" 2>/dev/null && print_status "Removed dangling images" || print_warning "No dangling images to remove"

# 6. Remove unused Docker volumes
echo ""
echo "6. Removing unused Docker volumes..."
docker volume prune -af 2>/dev/null && print_status "Removed unused volumes" || print_warning "No unused volumes"

# 7. Remove unused Docker networks
echo ""
echo "7. Removing unused Docker networks..."
docker network prune -af 2>/dev/null && print_status "Removed unused networks" || print_warning "No unused networks"

# 8. Clean up build cache (optional - commented out by default)
# echo ""
# echo "8. Cleaning Docker build cache..."
# docker builder prune -af 2>/dev/null && print_status "Cleaned build cache" || print_warning "Build cache cleanup failed"

# 9. Remove project-specific files
echo ""
echo "8. Cleaning up project files..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove Python cache files
find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && print_status "Removed __pycache__ directories" || true
find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null && print_status "Removed .pyc files" || true
find "$PROJECT_DIR" -type f -name "*.pyo" -delete 2>/dev/null && print_status "Removed .pyo files" || true

# Remove Python virtual environments
find "$PROJECT_DIR" -type d -name "venv" -exec rm -rf {} + 2>/dev/null && print_status "Removed venv directories" || true
find "$PROJECT_DIR" -type d -name ".venv" -exec rm -rf {} + 2>/dev/null && print_status "Removed .venv directories" || true

# Remove pytest cache
find "$PROJECT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null && print_status "Removed .pytest_cache directories" || true

# Remove node_modules
find "$PROJECT_DIR" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null && print_status "Removed node_modules directories" || true

# Remove Istio files
find "$PROJECT_DIR" -type d -name "*istio*" -o -name "*Istio*" 2>/dev/null | while read dir; do
    rm -rf "$dir" 2>/dev/null && print_status "Removed Istio directory: $dir" || true
done

# Remove .DS_Store (macOS)
find "$PROJECT_DIR" -type f -name ".DS_Store" -delete 2>/dev/null && print_status "Removed .DS_Store files" || true

# Remove temporary files
find "$PROJECT_DIR" -type f -name "*.tmp" -delete 2>/dev/null && print_status "Removed .tmp files" || true
find "$PROJECT_DIR" -type f -name "*.log" -not -path "*/\.git/*" -delete 2>/dev/null && print_status "Removed .log files" || true

# 10. Summary
echo ""
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
echo ""
echo "Docker Resources:"
docker system df 2>/dev/null | tail -n +2 || echo "Docker not available"
echo ""
print_status "Cleanup completed!"
echo ""
echo "To remove project images specifically, run:"
echo "  docker rmi log-ingestor:latest log-transformer:latest log-analyzer:latest 2>/dev/null || true"
echo ""
