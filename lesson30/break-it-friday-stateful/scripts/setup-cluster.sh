#!/bin/bash

set -euo pipefail

echo "Setting up local Kubernetes cluster for Break-It-Friday..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "ERROR: kind is not installed. Please install: https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl is not installed. Please install: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

CLUSTER_NAME="break-it-friday"

# Check if cluster already exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster ${CLUSTER_NAME} already exists. Delete it? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        kind delete cluster --name "${CLUSTER_NAME}"
    else
        echo "Using existing cluster"
        kubectl cluster-info --context "kind-${CLUSTER_NAME}"
        exit 0
    fi
fi

# Create kind cluster with extra mounts for local storage
cat <<YAML | kind create cluster --name "${CLUSTER_NAME}" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraMounts:
  - hostPath: /tmp/kind-pv
    containerPath: /mnt/data
- role: worker
- role: worker
- role: worker
YAML

echo "Cluster created successfully!"

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=60s

# Create StorageClass
echo "Creating StorageClass..."
kubectl apply -f ../k8s/storage/storageclass.yaml

# Create scenario namespaces
echo "Creating namespaces for scenarios..."
for i in {1..6}; do
    kubectl create namespace "scenario-0${i}" --dry-run=client -o yaml | kubectl apply -f -
done

echo ""
echo "✓ Cluster setup complete!"
echo "✓ Namespaces created: scenario-01 through scenario-06"
echo "✓ StorageClass 'fast-ssd-retain' available"
echo ""
echo "Next steps:"
echo "  1. Deploy broken scenarios: ./deploy-scenarios.sh"
echo "  2. Start debugging!"
