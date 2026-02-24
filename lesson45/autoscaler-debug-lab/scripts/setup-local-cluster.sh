#!/bin/bash

# Setup local Kubernetes cluster with Kind for autoscaler testing

set -euo pipefail

CLUSTER_NAME="${1:-autoscaler-debug}"

echo "Creating kind cluster: $CLUSTER_NAME"

cat <<KINDCONFIG | kind create cluster --name $CLUSTER_NAME --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
- role: worker
- role: worker
KINDCONFIG

echo ""
echo "Cluster created successfully!"
echo "kubectl cluster-info --context kind-$CLUSTER_NAME"

# Install metrics-server for HPA
echo ""
echo "Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for kind
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo ""
echo "Cluster setup complete!"
echo "Note: This is a local cluster. Cluster Autoscaler won't actually add cloud nodes."
echo "Use this for testing autoscaler logic and debugging scenarios."
