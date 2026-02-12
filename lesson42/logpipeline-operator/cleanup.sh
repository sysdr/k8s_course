#!/bin/bash

set -e

echo "=========================================="
echo "🧹 Docker Cleanup Script"
echo "=========================================="
echo ""

# Stop all running containers
echo "📦 Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all containers
echo "🗑️  Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all unused images
echo "🖼️  Removing unused images..."
docker image prune -a -f || echo "No unused images to remove"

# Remove all unused volumes
echo "💾 Removing unused volumes..."
docker volume prune -f || echo "No unused volumes to remove"

# Remove all unused networks
echo "🌐 Removing unused networks..."
docker network prune -f || echo "No unused networks to remove"

# Remove all build cache
echo "🧱 Removing build cache..."
docker builder prune -a -f || echo "No build cache to remove"

# Show system-wide disk usage
echo ""
echo "📊 Docker system disk usage:"
docker system df

echo ""
echo "✅ Cleanup completed!"
echo "=========================================="
