#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Building container images from: $PROJECT_ROOT"

# Check if Docker is available and daemon is running
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Cannot connect to the Docker daemon."
    echo ""
    echo "To fix this in WSL:"
    echo "  1. Install Docker Desktop for Windows (if not already installed)"
    echo "  2. Start Docker Desktop application on Windows"
    echo "  3. Enable WSL integration in Docker Desktop:"
    echo "     Settings > Resources > WSL Integration > Enable integration for your distro"
    echo "  4. Restart your WSL terminal after enabling integration"
    echo ""
    echo "Alternative: If you have Docker installed directly in WSL (not via Docker Desktop),"
    echo "  you may need to start it differently depending on your setup."
    echo ""
    exit 1
fi

# Check if kind is available
KIND_AVAILABLE=false
if command -v kind &> /dev/null; then
    KIND_AVAILABLE=true
    echo "kind found, will load images into cluster"
else
    echo "WARNING: kind not found in PATH. Images will be built but not loaded into kind cluster."
    echo "To install kind, run: ./scripts/install-kind.sh"
    echo "Or ensure kind is in your PATH if already installed."
fi

# Build all service images
services=(
    "vault-simulator"
    "log-ingestion-service"
    "log-processing-service"
    "analytics-api-service"
    "secrets-rotation-service"
)

for service in "${services[@]}"; do
    echo "Building $service..."
    docker build -t "$service:latest" "./services/$service"
    if [ "$KIND_AVAILABLE" = true ]; then
        echo "Loading $service into kind cluster..."
        kind load docker-image "$service:latest" --name secrets-platform || {
            echo "WARNING: Failed to load $service into kind cluster. Continuing..."
        }
    fi
done

# Build frontend
echo "Building frontend..."
docker build -t frontend:latest ./frontend
if [ "$KIND_AVAILABLE" = true ]; then
    echo "Loading frontend into kind cluster..."
    kind load docker-image frontend:latest --name secrets-platform || {
        echo "WARNING: Failed to load frontend into kind cluster. Continuing..."
    }
fi

if [ "$KIND_AVAILABLE" = true ]; then
    echo "All images built and loaded into kind cluster!"
else
    echo "All images built successfully!"
    echo "Note: Images were not loaded into kind cluster (kind not available)."
fi
