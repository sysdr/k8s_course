#!/bin/bash

echo "🧹 Cleaning up all Docker resources..."

# Stop all running containers
echo "Stopping containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "No running containers"

# Remove all containers
echo "Removing containers..."
docker rm my-nginx my-postgres static-website python-api 2>/dev/null || true

# Remove images
echo "Removing custom images..."
docker rmi static-website:latest python-api:latest demo:single-stage demo:multi-stage 2>/dev/null || true

# Remove volumes
echo "Removing volumes..."
docker volume rm postgres-data 2>/dev/null || true

# Prune system
echo "Pruning unused resources..."
docker system prune -f

echo "✅ Cleanup complete!"
