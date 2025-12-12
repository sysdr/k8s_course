#!/bin/bash
set -euo pipefail

# Demo script to generate metrics and test the platform
INGESTION_SVC="${INGESTION_SVC:-localhost:8000}"
PROCESSOR_SVC="${PROCESSOR_SVC:-localhost:8001}"
QUERY_SVC="${QUERY_SVC:-localhost:8002}"

echo "=========================================="
echo "Demo: Generating Log Entries and Metrics"
echo "=========================================="
echo ""

# Check if services are running
check_service() {
    local host_port=$1
    if curl -s -f "http://${host_port}/health" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

if ! check_service "${INGESTION_SVC}"; then
    echo "Error: log-ingestion service is not running at http://${INGESTION_SVC}"
    echo "Please start services first: ./scripts/startup.sh"
    exit 1
fi

echo "Services are ready. Generating logs..."
echo ""

# Function to send log entry
send_log() {
    local level=$1
    local service=$2
    local tenant=$3
    local message=$4
    local request_id=$(cat /proc/sys/kernel/random/uuid 2>/dev/null | tr -d '-' | cut -c1-8 || echo "req-$(date +%s)")
    local duration=$((RANDOM % 500 + 10))
    
    curl -s -X POST "http://${INGESTION_SVC}/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"${level}\",
            \"service\": \"${service}\",
            \"tenant\": \"${tenant}\",
            \"message\": \"${message}\",
            \"metadata\": {
                \"request_id\": \"${request_id}\",
                \"duration_ms\": ${duration}
            }
        }" > /dev/null 2>&1
}

# Generate logs for different tenants
echo "Generating logs for public tenant (20 entries)..."
for i in {1..20}; do
    send_log "INFO" "api-gateway" "public" "Request $i processed successfully"
    send_log "WARN" "api-gateway" "public" "Slow query detected in request $i"
    sleep 0.1
done
echo "✓ Public tenant logs generated"

echo ""
echo "Generating logs for payment tenant (15 entries)..."
for i in {1..15}; do
    send_log "INFO" "payment-processor" "payment" "Payment transaction $i completed"
    if [[ $((i % 5)) -eq 0 ]]; then
        send_log "ERROR" "payment-processor" "payment" "Failed to process transaction $i"
    fi
    sleep 0.1
done
echo "✓ Payment tenant logs generated"

echo ""
echo "Generating logs for system tenant (10 entries)..."
for i in {1..10}; do
    send_log "INFO" "system-monitor" "system" "System health check $i passed"
    sleep 0.1
done
echo "✓ System tenant logs generated"

echo ""
echo "=========================================="
echo "Demo log generation complete!"
echo "=========================================="
echo ""

# Fetch and display metrics
echo "Current metrics:"
METRICS=$(curl -s "http://${INGESTION_SVC}/metrics" 2>/dev/null || echo "{}")
if command -v jq &> /dev/null; then
    echo "$METRICS" | jq '.'
    PROCESSED=$(echo "$METRICS" | jq -r '.logs_processed_total // 0')
    FAILED=$(echo "$METRICS" | jq -r '.logs_failed_total // 0')
    echo ""
    echo "Summary:"
    echo "  - Logs processed: $PROCESSED"
    echo "  - Logs failed: $FAILED"
else
    echo "$METRICS"
fi

echo ""
echo "Check the dashboard to see updated metrics:"
echo "  http://localhost:3000 (if frontend is running)"
echo ""
echo "Or check metrics directly:"
echo "  curl http://${INGESTION_SVC}/metrics"
echo ""

