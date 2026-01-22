#!/bin/bash

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Kubernetes Logging System - Cleanup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop Kubernetes services
echo "1. Stopping Kubernetes services..."
kubectl delete namespace logging-system --ignore-not-found=true 2>/dev/null && echo "   ✓ Deleted logging-system namespace" || echo "   ℹ Namespace already deleted"

# Stop kind cluster
echo ""
echo "2. Stopping kind cluster..."
if kind get clusters 2>/dev/null | grep -q "logging-demo"; then
    kind delete cluster --name logging-demo 2>/dev/null && echo "   ✓ Deleted kind cluster 'logging-demo'" || echo "   ℹ Cluster already deleted"
else
    echo "   ℹ No kind cluster found"
fi

# Stop all running containers
echo ""
echo "3. Stopping Docker containers..."
RUNNING_CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
    docker stop $(docker ps -q) 2>/dev/null && echo "   ✓ Stopped $RUNNING_CONTAINERS running container(s)" || echo "   ℹ No containers to stop"
else
    echo "   ℹ No running containers"
fi

# Remove stopped containers
echo ""
echo "4. Removing stopped containers..."
STOPPED_CONTAINERS=$(docker ps -aq 2>/dev/null | wc -l)
if [ "$STOPPED_CONTAINERS" -gt 0 ]; then
    docker rm $(docker ps -aq) 2>/dev/null && echo "   ✓ Removed $STOPPED_CONTAINERS stopped container(s)" || echo "   ℹ No containers to remove"
else
    echo "   ℹ No stopped containers"
fi

# Remove unused images
echo ""
echo "5. Removing unused Docker images..."
docker image prune -af --filter "dangling=true" 2>/dev/null && echo "   ✓ Removed dangling images" || echo "   ℹ No dangling images"

# Remove unused volumes
echo ""
echo "6. Removing unused Docker volumes..."
docker volume prune -af 2>/dev/null && echo "   ✓ Removed unused volumes" || echo "   ℹ No unused volumes"

# Remove unused networks
echo ""
echo "7. Removing unused Docker networks..."
docker network prune -af 2>/dev/null && echo "   ✓ Removed unused networks" || echo "   ℹ No unused networks"

# System prune (optional - commented out by default)
# echo ""
# echo "8. Full system prune (all unused resources)..."
# docker system prune -af --volumes 2>/dev/null && echo "   ✓ System prune completed" || echo "   ℹ System prune failed"

# Kill port-forward processes
echo ""
echo "8. Stopping port-forward processes..."
pkill -f "kubectl port-forward" 2>/dev/null && echo "   ✓ Stopped port-forward processes" || echo "   ℹ No port-forward processes running"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Remaining Docker resources:"
echo "  Containers: $(docker ps -aq 2>/dev/null | wc -l)"
echo "  Images: $(docker images -q 2>/dev/null | wc -l)"
echo "  Volumes: $(docker volume ls -q 2>/dev/null | wc -l)"
echo ""
