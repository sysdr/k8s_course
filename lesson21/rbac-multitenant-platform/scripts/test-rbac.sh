#!/bin/bash
set -euo pipefail

echo "Testing RBAC permissions..."
echo ""

# Function to test permission
test_permission() {
    local sa=$1
    local ns=$2
    local resource=$3
    local verb=$4
    
    result=$(kubectl auth can-i "$verb" "$resource" \
        --as="system:serviceaccount:$ns:$sa" \
        -n "$ns" 2>/dev/null)
    
    if [ "$result" = "yes" ]; then
        echo "✓ $sa can $verb $resource in $ns"
    else
        echo "✗ $sa cannot $verb $resource in $ns"
    fi
}

echo "=== Log Processor ServiceAccount ==="
test_permission "log-processor-sa" "analytics" "pods" "get"
test_permission "log-processor-sa" "analytics" "pods" "list"
test_permission "log-processor-sa" "analytics" "pods/log" "get"
test_permission "log-processor-sa" "analytics" "secrets" "get"
test_permission "log-processor-sa" "analytics" "pods" "delete"

echo ""
echo "=== Analytics API ServiceAccount ==="
test_permission "analytics-api-sa" "analytics" "pods" "list"
test_permission "analytics-api-sa" "analytics" "deployments" "list"
test_permission "analytics-api-sa" "analytics" "roles" "list"
test_permission "analytics-api-sa" "analytics" "pods" "delete"

echo ""
echo "=== DevOps Team ServiceAccount ==="
test_permission "devops-team-sa" "devops" "pods" "create"
test_permission "devops-team-sa" "devops" "deployments" "update"
test_permission "devops-team-sa" "devops" "secrets" "get"

echo ""
echo "=== Developer Team ServiceAccount ==="
test_permission "developer-team-sa" "developers" "pods" "get"
test_permission "developer-team-sa" "developers" "pods" "list"
test_permission "developer-team-sa" "developers" "pods" "create"
test_permission "developer-team-sa" "developers" "secrets" "get"

echo ""
echo "=== Auditor ServiceAccount ==="
test_permission "auditor-sa" "auditors" "pods" "list"
test_permission "auditor-sa" "auditors" "events" "list"
test_permission "auditor-sa" "auditors" "pods" "delete"

echo ""
echo "Testing complete!"
