#!/bin/bash
set -euo pipefail

echo "Setting up local Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create kind cluster with custom configuration
cat <<KINDCONFIG | kind create cluster --name postgres-ha --config=-
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
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
- role: worker
KINDCONFIG

echo "Cluster created successfully!"
echo "Installing Istio..."

# Install Istio
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH
istioctl install --set profile=demo -y

# Enable Istio injection for namespaces
kubectl label namespace default istio-injection=enabled

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Installing helm..."
    mkdir -p ~/.local/bin
    curl -LO https://get.helm.sh/helm-v3.19.4-linux-amd64.tar.gz
    tar -zxvf helm-v3.19.4-linux-amd64.tar.gz
    mv linux-amd64/helm ~/.local/bin/helm
    chmod +x ~/.local/bin/helm
    rm -rf linux-amd64 helm-v3.19.4-linux-amd64.tar.gz
    export PATH=$HOME/.local/bin:$PATH
fi

# Ensure helm is in PATH
export PATH=$HOME/.local/bin:$PATH

echo "Installing Prometheus Operator..."
kubectl create namespace monitoring || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

echo "Cluster setup complete!"
