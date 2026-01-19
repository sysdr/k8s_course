#!/bin/bash

set -euo pipefail

echo "Triggering canary deployment..."

# Update order-service deployment to use v2 image
kubectl set image deployment/order-service \
  order-service=order-service:v2 \
  -n progressive-delivery

# Add annotation to trigger Flagger
kubectl annotate deployment/order-service \
  flagger.app/trigger="$(date +%s)" \
  -n progressive-delivery --overwrite

echo "✓ Canary triggered!"
echo ""
echo "Monitor progress:"
echo "  kubectl get canary order-service -n progressive-delivery -w"
echo "  kubectl describe canary order-service -n progressive-delivery"
echo ""
echo "View events:"
echo "  kubectl get events -n progressive-delivery --sort-by='.lastTimestamp'"
