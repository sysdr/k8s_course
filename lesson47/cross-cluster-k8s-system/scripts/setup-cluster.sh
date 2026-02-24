#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes clusters with kind..."

# Create Cluster A
echo "Creating Cluster A..."
kind create cluster --name cluster-a --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Create Cluster B
echo "Creating Cluster B..."
kind create cluster --name cluster-b --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
EOF

# Install MetalLB for LoadBalancer support in Cluster A
echo "Installing MetalLB in Cluster A..."
kubectl config use-context kind-cluster-a
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
kubectl wait --namespace metallb-system \
    --for=condition=ready pod \
    --selector=app=metallb \
    --timeout=90s

# Configure MetalLB IP range
kubectl apply -f - <<EOF
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.18.255.200-172.18.255.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: empty
  namespace: metallb-system
EOF

echo "Clusters created successfully!"
echo "Cluster A context: kind-cluster-a"
echo "Cluster B context: kind-cluster-b"
