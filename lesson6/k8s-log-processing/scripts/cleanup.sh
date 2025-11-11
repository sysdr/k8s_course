#!/bin/bash
set -euo pipefail

kubectl delete namespace log-processing --ignore-not-found=true
kubectl delete namespace monitoring --ignore-not-found=true
kind delete cluster --name log-processing

echo "Cleanup complete!"
