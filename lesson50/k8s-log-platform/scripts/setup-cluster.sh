#!/bin/bash
set -euo pipefail
# ─── Local Cluster Setup (kind) ──────────────────────────────────────────────

CLUSTER_NAME="${CLUSTER_NAME:-log-platform-local}"
K8S_VERSION="${K8S_VERSION:-v1.29.0}"

echo "Setting up local Kubernetes cluster: $CLUSTER_NAME"

command -v kind  >/dev/null 2>&1 || { echo "kind required: https://kind.sigs.k8s.io/docs/user/quick-start/"; exit 1; }
command -v helm  >/dev/null 2>&1 || { echo "helm required: https://helm.sh/docs/intro/install/"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl required"; exit 1; }

# Create kind cluster with multi-node config
cat > /tmp/kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
nodes:
  - role: control-plane
    image: kindest/node:${K8S_VERSION}
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
      - containerPort: 443
        hostPort: 8443
  - role: worker
    image: kindest/node:${K8S_VERSION}
  - role: worker
    image: kindest/node:${K8S_VERSION}
  - role: worker
    image: kindest/node:${K8S_VERSION}
EOF

kind create cluster --config /tmp/kind-config.yaml || echo "Cluster already exists"

# Install Nginx Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io --force-update
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Install Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.retention=7d

echo ""
echo "✅ Cluster ready: $CLUSTER_NAME"
echo "   kubectl cluster-info --context kind-${CLUSTER_NAME}"
echo "   Grafana: kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3001:80"
