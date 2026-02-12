#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "Cleanup Script - Docker and Kubernetes"
echo "=========================================="
echo ""

# Stop all port-forwards
echo "1. Stopping port-forward processes..."
pkill -f "kubectl port-forward" 2>/dev/null && echo "   ✓ Port-forwards stopped" || echo "   ℹ No port-forwards running"

# Stop and remove Kubernetes resources
echo ""
echo "2. Cleaning up Kubernetes resources..."
if kubectl get namespace log-platform &>/dev/null; then
    kubectl delete namespace log-platform --wait=true --timeout=60s 2>/dev/null && echo "   ✓ Namespace deleted" || echo "   ⚠ Namespace deletion in progress"
else
    echo "   ℹ Namespace already deleted"
fi

# Delete kind cluster
echo ""
echo "3. Deleting kind cluster..."
if kind get clusters | grep -q log-platform-cluster; then
    kind delete cluster --name log-platform-cluster 2>/dev/null && echo "   ✓ Kind cluster deleted" || echo "   ⚠ Cluster deletion failed"
else
    echo "   ℹ Kind cluster already deleted"
fi

# Stop all running containers
echo ""
echo "4. Stopping Docker containers..."
CONTAINERS=$(docker ps -q)
if [ -n "$CONTAINERS" ]; then
    docker stop $CONTAINERS 2>/dev/null && echo "   ✓ Containers stopped" || echo "   ⚠ Some containers may still be running"
else
    echo "   ℹ No running containers"
fi

# Remove all stopped containers
echo ""
echo "5. Removing stopped containers..."
docker container prune -f && echo "   ✓ Stopped containers removed" || echo "   ⚠ Container cleanup failed"

# Remove unused images
echo ""
echo "6. Removing unused Docker images..."
docker image prune -a -f && echo "   ✓ Unused images removed" || echo "   ⚠ Image cleanup failed"

# Remove unused volumes
echo ""
echo "7. Removing unused Docker volumes..."
docker volume prune -f && echo "   ✓ Unused volumes removed" || echo "   ⚠ Volume cleanup failed"

# Remove unused networks
echo ""
echo "8. Removing unused Docker networks..."
docker network prune -f && echo "   ✓ Unused networks removed" || echo "   ⚠ Network cleanup failed"

# Remove build cache
echo ""
echo "9. Removing Docker build cache..."
docker builder prune -f && echo "   ✓ Build cache removed" || echo "   ⚠ Build cache cleanup failed"

# Clean up project files
echo ""
echo "10. Cleaning up project files..."
PROJECT_DIR="/home/systemdr03/git/k8s_course/lesson41/k8s-cluster-autoscaler-demo"

# Remove node_modules
find "$PROJECT_DIR" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null && echo "   ✓ node_modules removed" || echo "   ℹ No node_modules found"

# Remove venv
find "$PROJECT_DIR" -type d -name "venv" -exec rm -rf {} + 2>/dev/null && echo "   ✓ venv removed" || echo "   ℹ No venv found"

# Remove .pytest_cache
find "$PROJECT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null && echo "   ✓ .pytest_cache removed" || echo "   ℹ No .pytest_cache found"

# Remove .pyc files and __pycache__
find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null && echo "   ✓ .pyc files removed" || echo "   ℹ No .pyc files found"
find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo "   ✓ __pycache__ directories removed" || echo "   ℹ No __pycache__ found"

# Remove Istio files
find "$PROJECT_DIR" -path "*/istio*" -type f -delete 2>/dev/null && echo "   ✓ Istio files removed" || echo "   ℹ No Istio files found"
find "$PROJECT_DIR" -path "*/istio*" -type d -exec rm -rf {} + 2>/dev/null && echo "   ✓ Istio directories removed" || echo "   ℹ No Istio directories found"

# Remove temporary files
echo ""
echo "11. Removing temporary files..."
rm -f /tmp/frontend-pf.log /tmp/grafana-pf.log /tmp/prometheus-pf.log 2>/dev/null && echo "   ✓ Temporary log files removed" || echo "   ℹ No temporary log files found"

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Summary:"
docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | head -5 || echo "No containers"
echo ""
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -5 || echo "No images"
echo ""
