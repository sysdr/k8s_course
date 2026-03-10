#!/bin/bash
set -euo pipefail
CONTEXT="${KUBE_CONTEXT:-kind-log-platform-local}"
NAMESPACE="${NAMESPACE:-log-platform}"
ENVIRONMENT="${ENVIRONMENT:-us-east-1}"

echo "Deploying to context: $CONTEXT, environment: $ENVIRONMENT"

# Apply namespace and base config first
kubectl --context="$CONTEXT" apply -f k8s/base/namespace.yaml
kubectl --context="$CONTEXT" apply -f k8s/base/configmaps/config.yaml

# Wait for namespace to be active
kubectl --context="$CONTEXT" wait --for=jsonpath="{.status.phase}=Active" \
  namespace/"$NAMESPACE" --timeout=30s

# Apply overlay via kustomize
kubectl --context="$CONTEXT" apply -k "k8s/overlays/${ENVIRONMENT}/"

# Wait for rollouts
for deployment in log-ingestion log-processor log-query frontend; do
  echo "Waiting for $deployment rollout..."
  kubectl --context="$CONTEXT" rollout status \
    deployment/"$deployment" -n "$NAMESPACE" --timeout=180s
done

echo ""
echo "✅ Deployment complete"
kubectl --context="$CONTEXT" get pods -n "$NAMESPACE"
