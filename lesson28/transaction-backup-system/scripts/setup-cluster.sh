#!/bin/bash
set -euo pipefail

echo "🚀 Setting up Kubernetes cluster..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "❌ kind not found. Install from: https://kind.sigs.k8s.io/"
    exit 1
fi

# Create kind cluster with extra port mappings
cat <<KINDCONFIG | kind create cluster --name transaction-system --config=-
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
KINDCONFIG

echo "✅ Cluster created successfully"

# Install Istio
echo "📦 Installing Istio..."
if ! command -v istioctl &> /dev/null; then
    echo "⚠️  istioctl not found. Install from: https://istio.io/latest/docs/setup/getting-started/"
    echo "Skipping Istio installation..."
else
    istioctl install --set profile=demo -y
    kubectl label namespace default istio-injection=enabled --overwrite
    echo "✅ Istio installed"
fi

# Install Velero CLI
echo "📦 Installing Velero..."
if ! command -v velero &> /dev/null; then
    echo "⚠️  velero CLI not found. Install from: https://velero.io/docs/main/basic-install/"
    echo "Skipping Velero installation..."
else
    # Install Velero with MinIO
    velero install \
        --provider aws \
        --plugins velero/velero-plugin-for-aws:v1.8.0 \
        --bucket velero-backups \
        --secret-file ./credentials-velero \
        --use-volume-snapshots=false \
        --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.minio:9000 \
        --use-restic || echo "⚠️ Velero installation failed, continuing..."
fi

echo "✅ Cluster setup complete!"
