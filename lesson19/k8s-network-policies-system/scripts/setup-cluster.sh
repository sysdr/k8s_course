#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster with Network Policy support..."

# Check for kind or minikube
if command -v kind &> /dev/null; then
    echo "Using kind..."
    cat <<KINDCONFIG > /tmp/kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
KINDCONFIG
    kind create cluster --name network-policies --config /tmp/kind-config.yaml
    
    # Install Calico for Network Policy support
    kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml
    
elif command -v minikube &> /dev/null; then
    echo "Using minikube..."
    minikube start --cni=calico --memory=8192 --cpus=4
else
    echo "Error: Neither kind nor minikube found. Please install one."
    exit 1
fi

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Install Istio
echo "Installing Istio..."
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.19.0 sh -
cd istio-1.19.0
export PATH=$PWD/bin:$PATH
istioctl install --set profile=default -y
cd ..

# Label kube-system namespace
kubectl label namespace kube-system name=kube-system

echo "✓ Cluster setup complete"
echo "✓ Calico CNI installed for Network Policy support"
echo "✓ Istio service mesh installed"
