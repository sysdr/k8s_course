#!/bin/bash
# Cleanup script to stop containers and remove unused Docker resources

set -euo pipefail

echo "=== Docker Cleanup Script ==="
echo ""

# Stop all running containers
echo "1. Stopping all running containers..."
docker ps -q | xargs -r docker stop 2>/dev/null || echo "   No running containers to stop"
echo "   ✓ Done"
echo ""

# Remove all containers
echo "2. Removing all containers..."
docker ps -a -q | xargs -r docker rm 2>/dev/null || echo "   No containers to remove"
echo "   ✓ Done"
echo ""

# Remove unused images
echo "3. Removing unused Docker images..."
docker image prune -a -f 2>/dev/null || echo "   No unused images to remove"
echo "   ✓ Done"
echo ""

# Remove unused volumes
echo "4. Removing unused volumes..."
docker volume prune -f 2>/dev/null || echo "   No unused volumes to remove"
echo "   ✓ Done"
echo ""

# Remove unused networks
echo "5. Removing unused networks..."
docker network prune -f 2>/dev/null || echo "   No unused networks to remove"
echo "   ✓ Done"
echo ""

# Remove build cache
echo "6. Removing build cache..."
docker builder prune -f 2>/dev/null || echo "   No build cache to remove"
echo "   ✓ Done"
echo ""

# Show remaining Docker resources
echo "=== Remaining Docker Resources ==="
echo "Containers:"
docker ps -a | wc -l | awk '{print "   "$1-1" container(s)"}'
echo "Images:"
docker images | wc -l | awk '{print "   "$1-1" image(s)"}'
echo "Volumes:"
docker volume ls | wc -l | awk '{print "   "$1-1" volume(s)"}'
echo ""

echo "=== Cleanup Complete ==="
