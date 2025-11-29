#!/bin/bash
set -euo pipefail

API_URL="${API_GATEWAY_URL:-http://localhost:30080}"

test_status() {
    echo "Testing /api/v1/status endpoint..."
    response=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/status" \
        -H "X-User-Id: test-user" \
        -H "X-Tier: free")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 200 ]; then
        echo "✓ Status endpoint working"
        echo "$body" | jq '.' || echo "$body"
        return 0
    else
        echo "✗ Status endpoint failed with code $http_code"
        return 1
    fi
}

test_process() {
    echo "Testing /api/v1/process endpoint..."
    response=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/process" \
        -H "Content-Type: application/json" \
        -H "X-User-Id: test-user" \
        -H "X-Tier: free" \
        -d '{"test": "data"}')
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 200 ]; then
        echo "✓ Process endpoint working"
        echo "$body" | jq '.' || echo "$body"
        return 0
    else
        echo "✗ Process endpoint failed with code $http_code"
        return 1
    fi
}

test_data() {
    echo "Testing /api/v1/data/{item_id} endpoint..."
    response=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/data/test-item-123" \
        -H "X-User-Id: test-user" \
        -H "X-Tier: free")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 200 ]; then
        echo "✓ Data endpoint working"
        echo "$body" | jq '.' || echo "$body"
        return 0
    else
        echo "✗ Data endpoint failed with code $http_code"
        return 1
    fi
}

test_metrics() {
    echo "Testing /metrics endpoint..."
    response=$(curl -s -w "\n%{http_code}" "${API_URL}/metrics")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" -eq 200 ]; then
        echo "✓ Metrics endpoint working"
        return 0
    else
        echo "✗ Metrics endpoint failed with code $http_code"
        return 1
    fi
}

# Run tests
echo "Running API integration tests..."
echo "API Gateway URL: $API_URL"
echo ""

failed=0
test_status || ((failed++))
test_process || ((failed++))
test_data || ((failed++))
test_metrics || ((failed++))

if [ $failed -eq 0 ]; then
    echo ""
    echo "All tests passed!"
    exit 0
else
    echo ""
    echo "$failed test(s) failed!"
    exit 1
fi
