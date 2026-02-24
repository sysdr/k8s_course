#!/bin/bash

# Cleanup all debugging resources

set -euo pipefail

echo "Cleaning up debugging resources..."

# Delete test deployments
kubectl delete deployment autoscaler-test --ignore-not-found=true
kubectl delete deployment resource-hungry-app --ignore-not-found=true -n default
kubectl delete deployment scale-test-deployment --ignore-not-found=true -n default
kubectl delete deployment gpu-workload --ignore-not-found=true -n default
kubectl delete deployment affinity-impossible --ignore-not-found=true -n default
kubectl delete deployment untolerated-workload --ignore-not-found=true -n default
kubectl delete deployment tolerated-workload --ignore-not-found=true -n default
kubectl delete deployment quota-blocked-app --ignore-not-found=true -n quota-limited

# Delete namespaces
kubectl delete namespace quota-limited --ignore-not-found=true

# Delete debugging autoscaler instances
kubectl delete deployment cluster-autoscaler-broken-iam --ignore-not-found=true -n kube-system

echo "Cleanup complete!"
