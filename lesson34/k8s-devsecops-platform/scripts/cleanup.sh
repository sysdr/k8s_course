#!/bin/bash

set -euo pipefail

echo "Cleaning up DevSecOps platform..."

# Delete all resources in namespace
kubectl delete namespace devsecops --ignore-not-found=true

# Delete security policies
kubectl delete clusterpolicy --all --ignore-not-found=true

echo "Cleanup complete!"
echo "To delete the cluster: kind delete cluster --name devsecops-cluster"
