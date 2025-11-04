#!/bin/bash
set -e
cd "$(dirname "$0")/.."
kubectl apply -f k8s/base/
echo "Deployment complete"
