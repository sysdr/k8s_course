#!/bin/bash
# setup-cluster.sh — Provision two kind clusters with proper topology labels
set -euo pipefail

CLUSTERS=("us-east" "eu-west")
REGIONS=("us-east-1" "eu-west-1")

for i in "${!CLUSTERS[@]}"; do
  CLUSTER="${CLUSTERS[$i]}"
  REGION="${REGIONS[$i]}"
  echo "Creating cluster: $CLUSTER (region: $REGION)"

  cat > /tmp/kind-${CLUSTER}.yaml << KINDEOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER}
nodes:
  - role: control-plane
  - role: worker
    labels:
      topology.kubernetes.io/region: ${REGION}
      topology.kubernetes.io/zone:   ${REGION}a
  - role: worker
    labels:
      topology.kubernetes.io/region: ${REGION}
      topology.kubernetes.io/zone:   ${REGION}b
  - role: worker
    labels:
      topology.kubernetes.io/region: ${REGION}
      topology.kubernetes.io/zone:   ${REGION}c
KINDEOF

  kind create cluster --config /tmp/kind-${CLUSTER}.yaml || echo "Cluster $CLUSTER already exists"
  echo "Installing Istio on $CLUSTER..."
  kubectl --context kind-${CLUSTER} create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -
  istioctl install --context kind-${CLUSTER} -y \
    --set profile=default \
    --set values.global.meshID=global-log-mesh \
    --set values.global.network=${CLUSTER}-network \
    --set values.global.multiCluster.clusterName=${CLUSTER}
  echo "✓ $CLUSTER ready"
done
echo "Both clusters provisioned. Set contexts:"
echo "  kubectl config use-context kind-us-east"
echo "  kubectl config use-context kind-eu-west"
