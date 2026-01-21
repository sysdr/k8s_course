#!/bin/bash

set -euo pipefail

echo "=========================================="
echo "Docker Cleanup Script"
echo "=========================================="
echo ""

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

# Step 1: Stop all running containers
print_info "Stopping all running containers..."
docker-compose down 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || print_warn "No containers to stop"

# Step 2: Remove all stopped containers
print_info "Removing all stopped containers..."
docker rm $(docker ps -aq) 2>/dev/null || print_warn "No containers to remove"

# Step 3: Remove all unused images
print_info "Removing unused Docker images..."
docker image prune -a -f || print_warn "No unused images to remove"

# Step 4: Remove all unused volumes
print_info "Removing unused Docker volumes..."
docker volume prune -f || print_warn "No unused volumes to remove"

# Step 5: Remove all unused networks
print_info "Removing unused Docker networks..."
docker network prune -f || print_warn "No unused networks to remove"

# Step 6: Remove build cache
print_info "Removing Docker build cache..."
docker builder prune -a -f || print_warn "No build cache to remove"

# Step 7: System prune (removes everything unused)
print_info "Performing system-wide cleanup..."
docker system prune -a -f --volumes || print_warn "System cleanup completed"

# Step 8: Clean up project-specific files
print_info "Cleaning up project files..."

# Remove node_modules
if [ -d "frontend/node_modules" ]; then
    print_info "Removing node_modules..."
    rm -rf frontend/node_modules
fi

# Remove venv directories
find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true

# Remove .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove Istio files
find . -type f -name "*istio*" -delete 2>/dev/null || true
find . -type d -name "*istio*" -exec rm -rf {} + 2>/dev/null || true

# Remove Docker build artifacts
rm -rf frontend/build 2>/dev/null || true
rm -rf frontend/.next 2>/dev/null || true

# Summary
echo ""
echo "=========================================="
print_info "Cleanup completed successfully!"
echo "=========================================="
echo ""
print_info "Docker resources cleaned:"
echo "  - Containers: Stopped and removed"
echo "  - Images: Unused images removed"
echo "  - Volumes: Unused volumes removed"
echo "  - Networks: Unused networks removed"
echo "  - Build cache: Cleared"
echo ""
print_info "Project files cleaned:"
echo "  - node_modules: Removed"
echo "  - venv: Removed"
echo "  - .pytest_cache: Removed"
echo "  - __pycache__: Removed"
echo "  - .pyc files: Removed"
echo "  - Istio files: Removed"
echo ""
