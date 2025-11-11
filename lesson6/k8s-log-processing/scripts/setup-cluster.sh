#!/bin/bash
set -euo pipefail

echo "Setting up Kubernetes cluster..."

if ! command -v kind &> /dev/null; then
    echo "kind not found. Install from: https://kind.sigs.k8s.io/"
    exit 1
fi

cat <<EOT | kind create cluster --name log-processing --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOT

echo "Installing Istio..."
if ! command -v istioctl &> /dev/null; then
    curl -L https://istio.io/downloadIstio | sh -
    export PATH=$PWD/istio-*/bin:$PATH
fi

istioctl install --set profile=demo -y

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "Cluster ready!"
