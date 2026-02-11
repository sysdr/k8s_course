#!/bin/bash
# Cleanup script for k8s-observability-debug project
# Stops containers, removes unused Docker resources, and cleans up project files

set -euo pipefail

echo "🧹 Starting cleanup process..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ============================================================================
# 1. Stop Kubernetes port-forwards
# ============================================================================
echo ""
echo "📡 Stopping kubectl port-forwards..."
pkill -f "kubectl port-forward" 2>/dev/null || true
echo "✅ Port-forwards stopped"

# ============================================================================
# 2. Stop Docker containers
# ============================================================================
echo ""
echo "🐳 Stopping Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all running containers
    docker ps -q | xargs -r docker stop 2>/dev/null || true
    echo "✅ Docker containers stopped"
else
    echo "⚠️  Docker not found, skipping container stop"
fi

# ============================================================================
# 3. Remove unused Docker resources
# ============================================================================
echo ""
echo "🧹 Cleaning up Docker resources..."
if command -v docker &> /dev/null; then
    # Remove stopped containers
    docker container prune -f 2>/dev/null || true
    
    # Remove unused images
    docker image prune -a -f 2>/dev/null || true
    
    # Remove unused volumes
    docker volume prune -f 2>/dev/null || true
    
    # Remove unused networks
    docker network prune -f 2>/dev/null || true
    
    # Remove build cache
    docker builder prune -a -f 2>/dev/null || true
    
    echo "✅ Docker resources cleaned"
else
    echo "⚠️  Docker not found, skipping Docker cleanup"
fi

# ============================================================================
# 4. Stop Docker service (if requested and running as root)
# ============================================================================
if [ "$EUID" -eq 0 ]; then
    echo ""
    echo "🛑 Stopping Docker service..."
    systemctl stop docker 2>/dev/null || service docker stop 2>/dev/null || true
    echo "✅ Docker service stopped"
else
    echo ""
    echo "ℹ️  Skipping Docker service stop (requires root privileges)"
fi

# ============================================================================
# 5. Clean up project files
# ============================================================================
echo ""
echo "📁 Cleaning up project files..."

# Remove node_modules
echo "  Removing node_modules directories..."
find . -type d -name "node_modules" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove Python virtual environments
echo "  Removing Python virtual environments..."
find . -type d -name "venv" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "env" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".env" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove Python cache files
echo "  Removing Python cache files..."
find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
find . -name ".Python" -delete 2>/dev/null || true

# Remove Istio files
echo "  Removing Istio files..."
find . -type d -name "*istio*" -prune -exec rm -rf {} + 2>/dev/null || true
find . -name "*istio*" -type f -delete 2>/dev/null || true

# Remove other common build/cache directories
echo "  Removing other build artifacts..."
find . -type d -name ".next" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "dist" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "build" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".cache" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".parcel-cache" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove log files
echo "  Removing log files..."
find . -name "*.log" -type f -delete 2>/dev/null || true
find . -name "*.log.*" -type f -delete 2>/dev/null || true

# Remove temporary files
echo "  Removing temporary files..."
find . -name "*.tmp" -type f -delete 2>/dev/null || true
find . -name "*.temp" -type f -delete 2>/dev/null || true
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
find . -name "Thumbs.db" -type f -delete 2>/dev/null || true

echo "✅ Project files cleaned"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "✨ Cleanup completed successfully!"
echo ""
echo "Summary:"
echo "  - Port-forwards: Stopped"
echo "  - Docker containers: Stopped"
echo "  - Docker resources: Cleaned"
if [ "$EUID" -eq 0 ]; then
    echo "  - Docker service: Stopped"
fi
echo "  - node_modules: Removed"
echo "  - Python venv/cache: Removed"
echo "  - Istio files: Removed"
echo "  - Build artifacts: Removed"
echo ""
echo "💡 To restart Docker service (as root):"
echo "   sudo systemctl start docker"
echo "   # or"
echo "   sudo service docker start"
echo ""
