#!/bin/bash
set -euo pipefail

# Demo script to generate log data for dashboard
# This script sends sample log entries to the log ingestion service

API_URL="${LOG_INGESTION_URL:-http://localhost:8000}"

echo "Starting demo log generation..."
echo "API URL: $API_URL"

# Check if service is available
if ! curl -s -f "${API_URL}/health" > /dev/null; then
    echo "Error: Log ingestion service is not available at ${API_URL}"
    echo "Please ensure the service is running and accessible"
    exit 1
fi

# Function to send a log entry
send_log() {
    local level=$1
    local service=$2
    local message=$3
    local metadata=$4
    
    local response=$(curl -s -X POST "${API_URL}/api/v1/logs" \
        -H "Content-Type: application/json" \
        -d "{
            \"level\": \"${level}\",
            \"service\": \"${service}\",
            \"message\": \"${message}\",
            \"metadata\": ${metadata}
        }" 2>&1)
    
    # Check if request failed
    if echo "$response" | grep -q "Internal Server Error\|error\|Error"; then
        echo "Warning: Failed to send log for ${service}" >&2
    fi
}

# Function to send batch logs
send_batch() {
    local count=$1
    local level=$2
    local service=$3
    
    local logs="["
    for i in $(seq 1 $count); do
        if [ $i -gt 1 ]; then
            logs+=","
        fi
        logs+="{
            \"level\": \"${level}\",
            \"service\": \"${service}\",
            \"message\": \"Batch log entry ${i} from ${service}\",
            \"metadata\": {\"batch_id\": \"batch-$(date +%s)\"}
        }"
    done
    logs+="]"
    
    curl -s -X POST "${API_URL}/api/v1/logs/batch" \
        -H "Content-Type: application/json" \
        -d "$logs" > /dev/null
}

# Services to simulate
SERVICES=("auth-service" "api-gateway" "payment-service" "user-service" "notification-service")
LEVELS=("DEBUG" "INFO" "WARNING" "ERROR" "CRITICAL")

echo "Sending initial batch of logs..."

# Send initial batch
for service in "${SERVICES[@]}"; do
    send_batch 50 "INFO" "$service"
    send_batch 10 "WARNING" "$service"
    send_batch 5 "ERROR" "$service"
done

echo "Sending continuous logs for 60 seconds..."
echo "Press Ctrl+C to stop early"

# Send continuous logs
for i in {1..60}; do
    for service in "${SERVICES[@]}"; do
        # Random level weighted towards INFO
        rand=$((RANDOM % 100))
        if [ $rand -lt 70 ]; then
            level="INFO"
        elif [ $rand -lt 85 ]; then
            level="WARNING"
        elif [ $rand -lt 95 ]; then
            level="ERROR"
        else
            level="CRITICAL"
        fi
        
        send_log "$level" "$service" "Demo log entry ${i} from ${service} at $(date +%H:%M:%S)" \
            "{\"request_id\": \"req-${RANDOM}\", \"user_id\": \"user-${RANDOM}\"}"
    done
    
    # Send a batch every 5 iterations
    if [ $((i % 5)) -eq 0 ]; then
        service=${SERVICES[$((RANDOM % ${#SERVICES[@]}))]}
        send_batch 20 "INFO" "$service"
    fi
    
    sleep 1
    echo -n "."
done

echo ""
echo "Demo complete!"
echo "Check the dashboard at http://localhost:3000 (or your frontend URL)"
echo "Total logs sent: ~$((${#SERVICES[@]} * 60 + ${#SERVICES[@]} * 65))"

