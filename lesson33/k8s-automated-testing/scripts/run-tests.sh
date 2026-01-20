#!/bin/bash

set -euo pipefail

echo "========================================"
echo "  Running Automated Test Suite"
echo "========================================"

# Run smoke tests
echo ""
echo "Running smoke tests..."
kubectl delete job smoke-tests -n ecommerce --ignore-not-found=true
kubectl apply -f k8s/jobs/smoke-tests.yaml
kubectl wait --for=condition=complete --timeout=300s job/smoke-tests -n ecommerce
echo "✓ Smoke tests passed"

# Run integration tests
echo ""
echo "Running integration tests..."
kubectl delete job integration-tests -n ecommerce --ignore-not-found=true
kubectl apply -f k8s/jobs/integration-tests.yaml
kubectl wait --for=condition=complete --timeout=600s job/integration-tests -n ecommerce
echo "✓ Integration tests passed"

# Run performance tests
echo ""
echo "Running performance tests..."
kubectl delete job performance-tests -n ecommerce --ignore-not-found=true
kubectl apply -f k8s/jobs/performance-tests.yaml
kubectl wait --for=condition=complete --timeout=900s job/performance-tests -n ecommerce || true
echo "✓ Performance tests completed"

# Check quality gates
echo ""
echo "Checking quality gates..."
kubectl port-forward -n ecommerce svc/test-results-aggregator 8003:8003 &
PF_PID=$!
sleep 5

GATE_RESULT=$(curl -s http://localhost:8003/api/v1/gate/check)
GATE_PASSED=$(echo $GATE_RESULT | jq -r '.gate_passed')
PASS_RATE=$(echo $GATE_RESULT | jq -r '.pass_rate')

kill $PF_PID

echo ""
echo "========================================"
echo "  Test Results Summary"
echo "========================================"
echo "Pass Rate: $PASS_RATE%"
echo "Quality Gate: $GATE_PASSED"
echo ""

if [ "$GATE_PASSED" = "true" ]; then
    echo "✓ All quality gates passed! Safe to deploy to production."
    exit 0
else
    echo "✗ Quality gates failed. Deployment blocked."
    exit 1
fi
