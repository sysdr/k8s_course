#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="debugging-challenge"
FAILED=0

echo "🧪 Running E-Commerce System Tests..."
echo "====================================="

# Test 1: Check pods are running
echo ""
echo "Test 1: Checking pod status..."
PODS_NOT_RUNNING=$(kubectl get pods -n ${NAMESPACE} -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null || echo "")
if [ -n "${PODS_NOT_RUNNING}" ]; then
    echo "  ❌ FAILED: Some pods are not running:"
    echo "    ${PODS_NOT_RUNNING}"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASSED: All pods are running"
fi

# Test 2: Check services have endpoints
echo ""
echo "Test 2: Checking service endpoints..."
SERVICES=$(kubectl get svc -n ${NAMESPACE} -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
for svc in ${SERVICES}; do
    ENDPOINTS=$(kubectl get endpoints ${svc} -n ${NAMESPACE} -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null || echo "")
    if [ -z "${ENDPOINTS}" ]; then
        echo "  ❌ FAILED: Service ${svc} has no endpoints"
        FAILED=$((FAILED + 1))
    else
        echo "  ✅ PASSED: Service ${svc} has endpoints: ${ENDPOINTS}"
    fi
done

# Test 3: Check backend health endpoint
echo ""
echo "Test 3: Testing backend health endpoint..."
HEALTH_RESPONSE=$(kubectl run test-health --rm -i --restart=Never \
    --image=curlimages/curl:latest \
    -n ${NAMESPACE} \
    -- curl -s http://backend-service:8080/health 2>/dev/null || echo "ERROR")
if echo "${HEALTH_RESPONSE}" | grep -q "healthy"; then
    echo "  ✅ PASSED: Backend health check successful"
else
    echo "  ❌ FAILED: Backend health check failed: ${HEALTH_RESPONSE}"
    FAILED=$((FAILED + 1))
fi

# Test 4: Check backend products endpoint
echo ""
echo "Test 4: Testing backend products endpoint..."
PRODUCTS_RESPONSE=$(kubectl run test-products --rm -i --restart=Never \
    --image=curlimages/curl:latest \
    -n ${NAMESPACE} \
    -- curl -s http://backend-service:8080/products 2>/dev/null || echo "ERROR")
if echo "${PRODUCTS_RESPONSE}" | grep -q "id"; then
    PRODUCT_COUNT=$(echo "${PRODUCTS_RESPONSE}" | grep -o '"id"' | wc -l)
    echo "  ✅ PASSED: Products endpoint returns ${PRODUCT_COUNT} products"
else
    echo "  ❌ FAILED: Products endpoint failed: ${PRODUCTS_RESPONSE}"
    FAILED=$((FAILED + 1))
fi

# Test 5: Check metrics endpoint
echo ""
echo "Test 5: Testing metrics endpoint..."
METRICS_RESPONSE=$(kubectl run test-metrics --rm -i --restart=Never \
    --image=curlimages/curl:latest \
    -n ${NAMESPACE} \
    -- curl -s http://backend-service:8080/metrics 2>/dev/null || echo "ERROR")
if echo "${METRICS_RESPONSE}" | grep -q "http_requests_total"; then
    REQUEST_COUNT=$(echo "${METRICS_RESPONSE}" | grep "http_requests_total" | wc -l)
    echo "  ✅ PASSED: Metrics endpoint returns ${REQUEST_COUNT} metric series"
else
    echo "  ❌ FAILED: Metrics endpoint failed or no metrics found"
    FAILED=$((FAILED + 1))
fi

# Test 6: Check for duplicate services
echo ""
echo "Test 6: Checking for duplicate services..."
DUPLICATE_SERVICES=$(kubectl get svc -n ${NAMESPACE} -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | sort | uniq -d)
if [ -n "${DUPLICATE_SERVICES}" ]; then
    echo "  ❌ FAILED: Duplicate services found:"
    echo "    ${DUPLICATE_SERVICES}"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASSED: No duplicate services found"
fi

# Test 7: Check metrics are non-zero after demo
echo ""
echo "Test 7: Checking metrics values are non-zero..."
if [ -f "${SCRIPT_DIR}/../.demo-run" ]; then
    METRICS_RESPONSE=$(kubectl run test-metrics-check --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        -n ${NAMESPACE} \
        -- curl -s http://backend-service:8080/metrics 2>/dev/null || echo "ERROR")
    REQUEST_TOTAL=$(echo "${METRICS_RESPONSE}" | grep "http_requests_total" | head -1 | grep -o '[0-9]*$' || echo "0")
    if [ "${REQUEST_TOTAL}" != "0" ] && [ -n "${REQUEST_TOTAL}" ]; then
        echo "  ✅ PASSED: Metrics show non-zero values (${REQUEST_TOTAL} requests)"
    else
        echo "  ⚠️  WARNING: Metrics may be zero. Run ./scripts/demo.sh first"
    fi
else
    echo "  ⚠️  SKIPPED: Demo not run yet. Run ./scripts/demo.sh first"
fi

# Summary
echo ""
echo "====================================="
if [ ${FAILED} -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ ${FAILED} test(s) failed"
    exit 1
fi
