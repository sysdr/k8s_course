#!/bin/bash
set -euo pipefail

echo "Cleaning up PostgreSQL HA system..."

# Delete all resources
kubectl delete -f k8s/base/services/ --ignore-not-found=true
kubectl delete -f k8s/base/pgbouncer/ --ignore-not-found=true
kubectl delete -f k8s/base/database/ --ignore-not-found=true
kubectl delete -f istio/ --ignore-not-found=true
kubectl delete -f monitoring/prometheus/ --ignore-not-found=true

# Delete namespaces
kubectl delete namespace database --ignore-not-found=true
kubectl delete namespace services --ignore-not-found=true

# Delete PVCs
kubectl delete pvc -n database -l app=postgres --ignore-not-found=true

echo "Cleanup complete!"
