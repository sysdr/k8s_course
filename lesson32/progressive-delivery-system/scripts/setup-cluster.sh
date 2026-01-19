#!/bin/bash

set -euo pipefail

echo "Setting up Kubernetes cluster for Progressive Delivery..."

# Check for kind
if ! command -v kind &> /dev/null; then
    echo "kind not found. Installing..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# Create cluster
echo "Creating kind cluster..."
cat <<EOT | kind create cluster --name progressive-delivery --config=-
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
EOT

# Install Istio
echo "Installing Istio..."
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH
istioctl install --set profile=demo -y
cd ..

# Install Flagger
echo "Installing Flagger..."
kubectl apply -k github.com/fluxcd/flagger//kustomize/istio

# Install metrics-server
echo "Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch -n kube-system deployment metrics-server --type=json -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

echo "✓ Cluster setup complete!"
echo "Use 'kubectl cluster-info' to verify"
