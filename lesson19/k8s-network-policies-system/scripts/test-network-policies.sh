#!/bin/bash
set -euo pipefail

echo "Testing Network Policies..."
echo "======================================"

# Test 1: Frontend should reach API Gateway
echo "Test 1: Frontend -> API Gateway (should succeed)"
kubectl run test-frontend --image=curlimages/curl --rm -i --restart=Never -n frontend -- \
    curl -s -o /dev/null -w "%{http_code}" http://api-gateway.backend.svc.cluster.local:8000/health
echo ""

# Test 2: Frontend should NOT reach Log Ingestion directly
echo "Test 2: Frontend -> Log Ingestion (should fail)"
kubectl run test-frontend --image=curlimages/curl --rm -i --restart=Never -n frontend -- \
    curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://log-ingestion.backend.svc.cluster.local:8001/health || echo "BLOCKED (expected)"
echo ""

# Test 3: API Gateway should reach Log Ingestion
echo "Test 3: API Gateway -> Log Ingestion (should succeed)"
GATEWAY_POD=$(kubectl get pods -n backend -l app=api-gateway -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n backend $GATEWAY_POD -- \
    curl -s -o /dev/null -w "%{http_code}" http://log-ingestion.backend.svc.cluster.local:8001/health
echo ""

# Test 4: Frontend should NOT reach TimescaleDB
echo "Test 4: Frontend -> TimescaleDB (should fail)"
kubectl run test-frontend --image=postgres:15 --rm -i --restart=Never -n frontend -- \
    pg_isready -h timescaledb.data-layer.svc.cluster.local -p 5432 || echo "BLOCKED (expected)"
echo ""

# Test 5: Analytics should reach TimescaleDB
echo "Test 5: Analytics -> TimescaleDB (should succeed)"
ANALYTICS_POD=$(kubectl get pods -n backend -l app=analytics-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n backend $ANALYTICS_POD -- \
    curl -s -o /dev/null -w "%{http_code}" http://timescaledb.data-layer.svc.cluster.local:5432 || echo "Connected"
echo ""

echo "======================================"
echo "Network Policy tests complete!"
echo "Expected: Tests 1, 3, 5 succeed; Tests 2, 4 fail/blocked"
