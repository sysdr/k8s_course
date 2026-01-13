#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_ROOT"

# Validate script paths before executing
if [ ! -f "$SCRIPT_DIR/setup-cluster.sh" ]; then
    echo "Error: setup-cluster.sh not found at $SCRIPT_DIR/setup-cluster.sh"
    exit 1
fi
if [ ! -f "$SCRIPT_DIR/build.sh" ]; then
    echo "Error: build.sh not found at $SCRIPT_DIR/build.sh"
    exit 1
fi
if [ ! -f "$SCRIPT_DIR/deploy.sh" ]; then
    echo "Error: deploy.sh not found at $SCRIPT_DIR/deploy.sh"
    exit 1
fi
if [ ! -f "$SCRIPT_DIR/test.sh" ]; then
    echo "Error: test.sh not found at $SCRIPT_DIR/test.sh"
    exit 1
fi

echo "Starting Kafka Pipeline system..."

# Check if cluster is set up
if ! kubectl get namespace kafka-pipeline &>/dev/null; then
    echo "Setting up cluster..."
    "$SCRIPT_DIR/setup-cluster.sh"
fi

# Build images if needed
echo "Building images..."
"$SCRIPT_DIR/build.sh"

# Deploy services
echo "Deploying services..."
"$SCRIPT_DIR/deploy.sh"

# Wait a bit for services to stabilize
echo "Waiting for services to stabilize..."
sleep 10

# Run tests
echo "Running tests..."
"$SCRIPT_DIR/test.sh"

echo "Startup complete!"
echo ""
echo "=== Dashboard Access ==="
echo "Run: kubectl port-forward -n kafka-pipeline svc/frontend 8080:80"
echo "Then open: http://localhost:8080"
