#!/bin/bash
set -euo pipefail

echo "=== Running Demo to Generate Dashboard Data ==="

# Get ingress gateway details
INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -z "$INGRESS_HOST" ]; then
    INGRESS_HOST="localhost"
fi

INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http")].port}' 2>/dev/null || echo "")
if [ -z "$INGRESS_PORT" ]; then
    INGRESS_PORT="80"
fi

# Check if port forwarding is needed
if [ "$INGRESS_HOST" = "localhost" ]; then
    # Try to get port-forward port
    PORT_FORWARD=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}' 2>/dev/null || echo "")
    if [ -n "$PORT_FORWARD" ]; then
        INGRESS_PORT="$PORT_FORWARD"
    fi
fi

echo "Sending demo requests to ${INGRESS_HOST}:${INGRESS_PORT}"

# Generate diverse log events with different severities and services
SEVERITIES=("INFO" "WARNING" "ERROR" "CRITICAL")
SERVICES=("api-service" "auth-service" "data-service" "notification-service" "payment-service")

# Send log events
for i in {1..200}; do
    SEVERITY=${SEVERITIES[$((RANDOM % ${#SEVERITIES[@]}))]}
    SERVICE=${SERVICES[$((RANDOM % ${#SERVICES[@]}))]}
    
    curl -s -X POST "http://${INGRESS_HOST}:${INGRESS_PORT}/api/v1/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"tenant_id\": \"demo-tenant\",
            \"service\": \"${SERVICE}\",
            \"severity\": \"${SEVERITY}\",
            \"message\": \"Demo log message ${i} from ${SERVICE} with severity ${SEVERITY}\",
            \"metadata\": {
                \"request_id\": \"req-$(printf %06d $i)\",
                \"user_id\": \"user-$(($RANDOM % 1000 + 1))\",
                \"session_id\": \"session-$(($RANDOM % 100 + 1))\"
            }
        }" > /dev/null 2>&1 || true
    
    # Show progress every 50 requests
    if [ $((i % 50)) -eq 0 ]; then
        echo "  Sent ${i} log events..."
    fi
done

echo ""
echo "✓ Demo complete! Sent 200 log events"
echo ""
echo "Waiting 10 seconds for processing..."
sleep 10

echo ""
echo "Checking statistics..."
curl -s "http://${INGRESS_HOST}:${INGRESS_PORT}/api/v1/statistics?tenant_id=demo-tenant&hours=24" | python3 -m json.tool 2>/dev/null || echo "Statistics endpoint may not be ready yet"

echo ""
echo "Dashboard should now show non-zero values!"
echo "Access dashboard at: http://${INGRESS_HOST}:${INGRESS_PORT}/"

