#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting all microservices..."
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start services in background
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    
    if check_port $port; then
        echo "⚠️  Port $port is already in use. Skipping $service_name"
        return 1
    fi
    
    echo "Starting $service_name..."
    cd "$PROJECT_ROOT"
    nohup bash "$script_path" > "${PROJECT_ROOT}/logs/${service_name}.log" 2>&1 &
    echo $! > "${PROJECT_ROOT}/logs/${service_name}.pid"
    echo "  ✓ $service_name started (PID: $(cat ${PROJECT_ROOT}/logs/${service_name}.pid))"
    sleep 2
}

# Create logs directory
mkdir -p "${PROJECT_ROOT}/logs"

# Start all services
start_service "log-ingester" "${SCRIPT_DIR}/startup-log-ingester.sh" 8000
start_service "log-processor" "${SCRIPT_DIR}/startup-log-processor.sh" 8001
start_service "log-api" "${SCRIPT_DIR}/startup-log-api.sh" 8002

echo ""
echo "All services started!"
echo "Check logs in: ${PROJECT_ROOT}/logs/"
echo ""
echo "To stop all services: ./scripts/stop-all.sh"
echo "To check service status: ./scripts/check-services.sh"
