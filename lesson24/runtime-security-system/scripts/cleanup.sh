#!/bin/bash
set -euo pipefail

echo "Cleaning up runtime security system..."

kubectl delete namespace runtime-security --ignore-not-found=true
kubectl delete clusterrole incident-response-role falco --ignore-not-found=true
kubectl delete clusterrolebinding incident-response-binding falco --ignore-not-found=true

echo "✓ Cleanup complete"
