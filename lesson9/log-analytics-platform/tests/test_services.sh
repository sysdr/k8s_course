#!/bin/bash
set -euo pipefail

echo "Testing log analytics platform services..."

NAMESPACE="log-analytics"
API_URL="http://localhost:30080"

# Test 1: All pods running
echo "Test 1: Checking if all pods are running..."
EXPECTED_PODS=13  # 3 api-gateway + 5 log-ingestion + 3 log-processor + 2 query-service + 2 frontend (minimum)
RUNNING_PODS=$(kubectl get pods -n ${NAMESPACE} --field-selector=status.phase=Running --no-headers | wc -l)

if [ "$RUNNING_PODS" -ge "$EXPECTED_PODS" ]; then
    echo "✓ All pods running (${RUNNING_PODS} pods)"
else
    echo "✗ Not enough pods running (${RUNNING_PODS}/${EXPECTED_PODS})"
    exit 1
fi

# Test 2: Services created
echo "Test 2: Checking services..."
SERVICES="api-gateway log-ingestion log-processor query-service frontend"
for svc in $SERVICES; do
    if kubectl get svc ${svc} -n ${NAMESPACE} &> /dev/null; then
        echo "✓ Service ${svc} exists"
    else
        echo "✗ Service ${svc} not found"
        exit 1
    fi
done

# Test 3: Health checks
echo "Test 3: Testing health endpoints..."
sleep 10  # Wait for services to be ready

if curl -sf ${API_URL}/health > /dev/null; then
    echo "✓ API Gateway health check passed"
else
    echo "✗ API Gateway health check failed"
    exit 1
fi

# Test 4: Log ingestion
echo "Test 4: Testing log ingestion..."
RESPONSE=$(curl -sf -X POST ${API_URL}/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "test",
    "message": "Integration test log"
  }' || echo "failed")

if [ "$RESPONSE" != "failed" ]; then
    echo "✓ Log ingestion successful"
else
    echo "✗ Log ingestion failed"
    exit 1
fi

# Test 5: Query logs
echo "Test 5: Testing log query..."
RESPONSE=$(curl -sf -X POST ${API_URL}/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 5
  }' || echo "failed")

if [ "$RESPONSE" != "failed" ]; then
    echo "✓ Log query successful"
else
    echo "✗ Log query failed"
    exit 1
fi

# Test 6: HPA configured
echo "Test 6: Checking HPA..."
if kubectl get hpa -n ${NAMESPACE} | grep -q "api-gateway-hpa"; then
    echo "✓ HPA configured"
else
    echo "✗ HPA not found"
    exit 1
fi

# Test 7: Network policies
echo "Test 7: Checking network policies..."
NP_COUNT=$(kubectl get networkpolicies -n ${NAMESPACE} --no-headers | wc -l)
if [ "$NP_COUNT" -ge 4 ]; then
    echo "✓ Network policies configured (${NP_COUNT} policies)"
else
    echo "✗ Insufficient network policies (${NP_COUNT}/4)"
    exit 1
fi

echo ""
echo "=========================================="
echo "All tests passed! ✓"
echo "=========================================="
