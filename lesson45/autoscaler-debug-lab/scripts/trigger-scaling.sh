#!/bin/bash

# Trigger autoscaler by creating resource-intensive workload

set -euo pipefail

REPLICAS="${1:-30}"
CPU="${2:-1000m}"
MEMORY="${3:-2Gi}"

echo "Creating deployment with $REPLICAS replicas requiring $CPU CPU and $MEMORY memory each"

kubectl create deployment autoscaler-test \
  --image=nginx:alpine \
  --replicas=$REPLICAS \
  --dry-run=client -o yaml | \
kubectl set resources -f - \
  --requests=cpu=$CPU,memory=$MEMORY \
  --limits=cpu=$CPU,memory=$MEMORY \
  --local -o yaml | \
kubectl apply -f -

echo ""
echo "Monitoring pod status..."
kubectl get pods -l app=autoscaler-test -w
