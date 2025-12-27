#!/bin/bash
set -euo pipefail

echo "Checking for duplicate services..."

# Check for running pods
echo "Running pods:"
kubectl get pods | grep -E "(log-ingestion|log-processor|api-gateway|frontend|NAME)" || echo "No pods found"

# Check for duplicate services
echo -e "\nChecking services:"
kubectl get svc -o wide

echo -e "\nChecking deployments:"
kubectl get deployments
