#!/bin/bash
set -euo pipefail

echo "Testing container networking patterns..."

# Test service discovery
echo "1. Testing DNS-based service discovery..."
kubectl run test-pod --image=busybox:1.36 --restart=Never -n log-system -- sleep 3600
kubectl wait --for=condition=ready pod/test-pod -n log-system --timeout=60s

# Resolve service DNS
kubectl exec -n log-system test-pod -- nslookup log-processor
kubectl exec -n log-system test-pod -- nslookup log-processor.log-system.svc.cluster.local

# Test connectivity
echo "2. Testing pod-to-service connectivity..."
kubectl exec -n log-system test-pod -- wget -O- http://log-processor:8080/health

# Test network policies
echo "3. Verifying network policy enforcement..."
kubectl get networkpolicies -n log-system

# Cleanup
kubectl delete pod test-pod -n log-system --force

echo "Network tests complete!"
