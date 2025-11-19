#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

SOLUTION="${1:-all}"

echo "Applying solutions..."

if [ "$SOLUTION" == "all" ] || [ "$SOLUTION" == "1" ]; then
    echo "Applying Solution 1: Resource Exhaustion Fix"
    kubectl apply -f "${PROJECT_ROOT}/k8s/solutions/01-resource-exhaustion-fixed.yaml"
fi

if [ "$SOLUTION" == "all" ] || [ "$SOLUTION" == "2" ]; then
    echo "Applying Solution 2: Selector Mismatch Fix"
    kubectl apply -f "${PROJECT_ROOT}/k8s/solutions/02-selector-mismatch-fixed.yaml"
fi

if [ "$SOLUTION" == "all" ] || [ "$SOLUTION" == "3" ]; then
    echo "Applying Solution 3: NetworkPolicy DNS Fix"
    kubectl apply -f "${PROJECT_ROOT}/k8s/solutions/03-network-policy-dns-fixed.yaml"
fi

if [ "$SOLUTION" == "all" ] || [ "$SOLUTION" == "4" ]; then
    echo "Applying Solution 4: Port Mismatch Fix"
    kubectl apply -f "${PROJECT_ROOT}/k8s/solutions/04-port-mismatch-fixed.yaml"
fi

if [ "$SOLUTION" == "all" ] || [ "$SOLUTION" == "5" ]; then
    echo "Applying Solution 5: Taint/Toleration Fix"
    kubectl apply -f "${PROJECT_ROOT}/k8s/solutions/05-taint-toleration-fixed.yaml"
fi

echo ""
echo "Solutions applied. Check Pod status:"
echo "  kubectl get pods -n log-processor"
