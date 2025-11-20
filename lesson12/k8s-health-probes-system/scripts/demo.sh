#!/bin/bash
set -euo pipefail

# Demo script to generate log data for dashboard
# This script sends sample logs to the log collector service

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

# Get service URL
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
COLLECTOR_URL="${COLLECTOR_URL:-http://localhost:8081}"

# Check if service is available
check_service() {
    local url=$1
    local name=$2
    
    if curl -sf "${url}/health/live" > /dev/null 2>&1; then
        log_info "${name} is available at ${url}"
        return 0
    else
        log_error "${name} is not available at ${url}"
        return 1
    fi
}

# Send log entry
send_log() {
    local level=$1
    local service=$2
    local message=$3
    local metadata=$4
    
    curl -s -X POST "${COLLECTOR_URL}/logs" \
        -H "Content-Type: application/json" \
        -d "{
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"level\": \"${level}\",
            \"service\": \"${service}\",
            \"message\": \"${message}\",
            \"metadata\": ${metadata}
        }" > /dev/null
}

log_info "Starting demo data generation..."

# Check if collector is available
if ! check_service "${COLLECTOR_URL}" "Log Collector"; then
    log_error "Log Collector is not available. Please start the services first."
    log_info "You can use: docker-compose up -d"
    exit 1
fi

# Generate sample logs
log_info "Generating sample log entries..."

# Generate logs from different services
SERVICES=("web-server" "api-gateway" "database" "cache" "auth-service" "payment-service")
LEVELS=("INFO" "WARNING" "ERROR" "DEBUG" "CRITICAL")

for i in {1..50}; do
    service=${SERVICES[$((RANDOM % ${#SERVICES[@]}))]}
    level=${LEVELS[$((RANDOM % ${#LEVELS[@]}))]}
    
    case $level in
        "ERROR")
            message="Failed to process request: Connection timeout after 30s"
            metadata='{"error_code": 500, "retry_count": 3}'
            ;;
        "WARNING")
            message="High memory usage detected: 85%"
            metadata='{"memory_usage": 85, "threshold": 80}'
            ;;
        "CRITICAL")
            message="Database connection pool exhausted"
            metadata='{"pool_size": 0, "max_pool": 100}'
            ;;
        "DEBUG")
            message="Processing request ID: req-${i}"
            metadata="{\"request_id\": \"req-${i}\", \"duration_ms\": $((RANDOM % 1000))}"
            ;;
        *)
            message="Request processed successfully"
            metadata="{\"status_code\": 200, \"duration_ms\": $((RANDOM % 500))}"
            ;;
    esac
    
    send_log "${level}" "${service}" "${message}" "${metadata}"
    
    if [ $((i % 10)) -eq 0 ]; then
        log_info "Sent ${i} log entries..."
    fi
done

log_info "Demo data generation complete!"
log_info "Sent 50 log entries to the collector"
log_info "Check the dashboard at ${FRONTEND_URL} to see the metrics update"

