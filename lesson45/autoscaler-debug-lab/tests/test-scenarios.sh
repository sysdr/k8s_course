#!/bin/bash

# Automated test suite for autoscaler debugging scenarios

set -euo pipefail

PASSED=0
FAILED=0

test_scenario() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing: $name... "
    
    if eval "$command" | grep -q "$expected"; then
        echo "✓ PASSED"
        PASSED=$((PASSED + 1))
    else
        echo "✗ FAILED"
        FAILED=$((FAILED + 1))
    fi
}

echo "Running Autoscaler Scenario Tests"
echo "=================================="

# Test 1: Autoscaler deployment exists
test_scenario "Autoscaler Deployment" \
    "kubectl get deployment cluster-autoscaler -n kube-system" \
    "cluster-autoscaler"

# Test 2: ServiceMonitor created
test_scenario "Metrics ServiceMonitor" \
    "kubectl get servicemonitor -n kube-system" \
    "cluster-autoscaler"

# Test 3: IAM role annotation
test_scenario "IAM Role Annotation" \
    "kubectl get sa cluster-autoscaler -n kube-system -o yaml" \
    "eks.amazonaws.com/role-arn"

echo ""
echo "=================================="
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo "=================================="

exit $FAILED
