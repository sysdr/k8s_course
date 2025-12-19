#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Setting up local Kubernetes cluster from: $PROJECT_ROOT"

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "kind is not installed. Installing kind..."
    "$SCRIPT_DIR/install-kind.sh"
    # Ensure PATH includes ~/.local/bin
    export PATH="$HOME/.local/bin:$PATH"
    # Verify installation was successful
    if ! command -v kind &> /dev/null; then
        echo "Failed to install kind. Please install manually:"
        echo "https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
        exit 1
    fi
fi

# Delete existing cluster if it exists
if kind get clusters 2>/dev/null | grep -q "^secrets-platform$"; then
    echo "Existing cluster 'secrets-platform' found. Deleting it..."
    kind delete cluster --name secrets-platform
fi

# Create kind cluster
echo "Creating kind cluster..."
cat <<YAML | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: secrets-platform
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
YAML

echo "Cluster created successfully!"

# Install Istio
echo "Installing Istio..."
ISTIO_DIR=$(mktemp -d)
cd "$ISTIO_DIR"
curl -L https://istio.io/downloadIstio | sh -
cd istio-*/bin
./istioctl install --set profile=demo -y
cd "$PROJECT_ROOT"

echo "Setup complete!"
echo "Run './scripts/build.sh' to build container images"
echo "Then run './scripts/deploy.sh' to deploy the platform"
