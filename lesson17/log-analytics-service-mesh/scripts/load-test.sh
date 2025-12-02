#!/bin/bash
set -euo pipefail

echo "=== Running Load Test ==="

INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$INGRESS_HOST" ]; then
    INGRESS_HOST="localhost"
fi

INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http")].port}')
if [ -z "$INGRESS_PORT" ]; then
    INGRESS_PORT="80"
fi

echo "Sending test requests to ${INGRESS_HOST}:${INGRESS_PORT}"

# Send sample log events
for i in {1..100}; do
    curl -X POST "http://${INGRESS_HOST}:${INGRESS_PORT}/api/v1/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"tenant_id\": \"demo-tenant\",
            \"service\": \"test-service\",
            \"severity\": \"INFO\",
            \"message\": \"Test log message ${i}\"
        }" &
done

wait

echo "✓ Load test complete"
echo "View results in Kiali dashboard: istioctl dashboard kiali"
