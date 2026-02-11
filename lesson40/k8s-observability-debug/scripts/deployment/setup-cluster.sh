#!/bin/bash
set -euo pipefail

echo "🎯 Setting up local Kubernetes cluster for observability debugging..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "❌ kind not found. Please install: https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

# Create kind cluster with specific configuration
cat <<EOFKIND | kind create cluster --name observability-debug --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  # Port mappings removed - using port-forwarding instead
  # extraPortMappings:
  # - containerPort: 80
  #   hostPort: 8080
  #   protocol: TCP
  # - containerPort: 443
  #   hostPort: 8443
  #   protocol: TCP
- role: worker
- role: worker
EOFKIND

echo "✅ Cluster created!"

# Install Prometheus CRDs
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml

echo "✅ Prometheus CRDs installed"
