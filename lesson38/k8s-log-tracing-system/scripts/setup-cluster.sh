#!/bin/bash
set -euo pipefail
# setup-cluster.sh — spin up a kind cluster with Istio and load images.

CLUSTER_NAME="k8s-log-tracing"

echo "=== Checking prerequisites …"
command -v kind   || { echo "ERROR: kind not installed"; exit 1; }
command -v kubectl || { echo "ERROR: kubectl not installed"; exit 1; }
command -v istioctl || { echo "WARNING: istioctl not found — Istio setup will be skipped"; }
command -v helm   || { echo "ERROR: helm not installed"; exit 1; }

echo "=== Creating kind cluster: ${CLUSTER_NAME}"
kind create cluster --name "${CLUSTER_NAME}" --config /dev/stdin <<'KINDCONF'
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        apiServer:
          extraArgs:
            enable-aggregated-apiservices: "true"
  - role: worker
  - role: worker
KINDCONF

kubectl config use-context "kind-${CLUSTER_NAME}"

echo "=== Creating namespaces …"
for ns in app messaging observability; do
  kubectl create namespace "${ns}" --dry-run=client -o yaml | kubectl apply -f -
done

echo "=== Labelling app namespace for Istio sidecar injection …"
kubectl label namespace app istio-injection=enabled --overwrite

echo "=== Installing Istio (if istioctl available) …"
if command -v istioctl &>/dev/null; then
  istioctl install --set profile=demo -y
  kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/kiali.yaml 2>/dev/null || true
else
  echo "SKIP: istioctl not found."
fi

echo "=== Loading Docker images into kind …"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/build.sh"
kind load docker-image log-ingestor:latest       --name "${CLUSTER_NAME}"
kind load docker-image log-processor:latest     --name "${CLUSTER_NAME}"
kind load docker-image analytics-service:latest --name "${CLUSTER_NAME}"
kind load docker-image frontend:latest          --name "${CLUSTER_NAME}"

echo ""
echo "=== Cluster ready.  Next: ./scripts/deploy.sh"
