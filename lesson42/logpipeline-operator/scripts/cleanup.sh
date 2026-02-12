#!/bin/bash

set -euo pipefail

echo "Cleaning up LogPipeline Operator system..."

# Delete example LogPipeline
kubectl delete -f k8s/base/example-logpipeline.yaml --ignore-not-found=true

# Delete infrastructure
kubectl delete -f k8s/base/ --ignore-not-found=true

# Delete monitoring
kubectl delete -f k8s/monitoring/ --ignore-not-found=true

# Delete operator
kubectl delete -f k8s/operator/ --ignore-not-found=true

# Delete CRDs
kubectl delete -f k8s/crds/ --ignore-not-found=true

# Delete namespaces
kubectl delete namespace logging --ignore-not-found=true
kubectl delete namespace logging-system --ignore-not-found=true

echo "Cleanup complete!"
