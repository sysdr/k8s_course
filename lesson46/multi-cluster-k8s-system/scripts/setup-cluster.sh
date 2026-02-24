#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Setting up local Kubernetes cluster with Kind..."

# Create multi-cluster setup
cat <<EOT | kind create cluster --name control-plane --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 6443
    hostPort: 6443
EOT

cat <<EOT | kind create cluster --name cluster-us-west --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOT

cat <<EOT | kind create cluster --name cluster-eu-west --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOT

cat <<EOT | kind create cluster --name cluster-ap-southeast --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
EOT

echo "Installing Karmada on control plane..."
kubectl config use-context kind-control-plane
helm repo add karmada https://github.com/karmada-io/karmada/charts
helm install karmada karmada/karmada --namespace karmada-system --create-namespace

echo "Joining member clusters to Karmada..."
karmadactl join cluster-us-west --cluster-kubeconfig=$HOME/.kube/config --cluster-context=kind-cluster-us-west
karmadactl join cluster-eu-west --cluster-kubeconfig=$HOME/.kube/config --cluster-context=kind-cluster-eu-west
karmadactl join cluster-ap-southeast --cluster-kubeconfig=$HOME/.kube/config --cluster-context=kind-cluster-ap-southeast

echo "Multi-cluster setup complete!"
