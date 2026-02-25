#!/bin/bash
# deploy.sh — Deploy full platform to target cluster
set -euo pipefail
CLUSTER="${1:-us-east}"
REGION="${2:-us-east}"
CONTEXT="kind-${CLUSTER}"

echo "Deploying to cluster: ${CLUSTER} (region: ${REGION}) context: ${CONTEXT}"

kubectl --context "${CONTEXT}" apply -k ../k8s/base/namespaces/
kubectl --context "${CONTEXT}" apply -k ../k8s/base/

helm upgrade --install log-platform ../helm/log-platform \
  --kube-context "${CONTEXT}" \
  --namespace log-processing \
  --create-namespace \
  --set global.region="${REGION}" \
  --wait \
  --timeout 10m

kubectl --context "${CONTEXT}" apply -f ../k8s/istio/

echo "✓ Deployment complete on ${CLUSTER}"
echo "Checking rollout status..."
kubectl --context "${CONTEXT}" rollout status deployment/log-ingestion -n log-processing
kubectl --context "${CONTEXT}" rollout status deployment/log-processor  -n log-processing
