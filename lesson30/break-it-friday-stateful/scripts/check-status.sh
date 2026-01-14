#!/bin/bash

set -euo pipefail

echo "========================================="
echo "Break-It-Friday: Scenario Status Check"
echo "========================================="
echo ""

for ns in scenario-01 scenario-02 scenario-03 scenario-04 scenario-05 scenario-06; do
    echo "--- $ns ---"
    
    # Pods
    echo "Pods:"
    kubectl get pods -n "$ns" 2>/dev/null || echo "  No pods found"
    
    # PVCs
    echo "PVCs:"
    kubectl get pvc -n "$ns" 2>/dev/null || echo "  No PVCs found"
    
    echo ""
done

echo "StorageClasses:"
kubectl get storageclass

echo ""
echo "========================================="
