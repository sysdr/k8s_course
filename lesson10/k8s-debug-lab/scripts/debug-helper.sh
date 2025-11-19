#!/bin/bash
set -euo pipefail

NAMESPACE="${1:-log-processor}"

echo "=========================================="
echo "K8s Debug Lab - Diagnostic Helper"
echo "=========================================="
echo ""

# Check Pending Pods
echo "[1] Pending Pods:"
kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Pending -o wide 2>/dev/null || echo "  None found"
echo ""

# Check Pod Events for failures
echo "[2] Recent Events (Warnings only):"
kubectl get events -n "$NAMESPACE" --field-selector=type=Warning --sort-by='.lastTimestamp' | tail -20
echo ""

# Check Services with no endpoints
echo "[3] Services with Zero Endpoints:"
for svc in $(kubectl get svc -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}'); do
    endpoints=$(kubectl get endpoints "$svc" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses}' 2>/dev/null)
    if [ -z "$endpoints" ]; then
        echo "  - $svc (no endpoints)"
    fi
done
echo ""

# Check ResourceQuota usage
echo "[4] ResourceQuota Usage:"
kubectl describe resourcequota -n "$NAMESPACE" 2>/dev/null | grep -A 10 "Used" || echo "  No ResourceQuota found"
echo ""

# Check Network Policies
echo "[5] NetworkPolicies:"
kubectl get networkpolicies -n "$NAMESPACE" 2>/dev/null || echo "  None found"
echo ""

# Check node resources
echo "[6] Node Resource Availability:"
kubectl top nodes 2>/dev/null || echo "  Metrics server not available"
echo ""

echo "=========================================="
echo "Common Debug Commands:"
echo "=========================================="
echo "• Describe pending pod:    kubectl describe pod <pod> -n $NAMESPACE"
echo "• Check node labels:       kubectl get nodes --show-labels"
echo "• Check node taints:       kubectl describe nodes | grep Taints"
echo "• Test DNS resolution:     kubectl run test --rm -it --image=busybox -- nslookup <service>"
echo "• Check endpoint:          kubectl get endpoints <service> -n $NAMESPACE"
echo "• View quota:              kubectl describe resourcequota -n $NAMESPACE"
