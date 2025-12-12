#!/bin/bash
set -euo pipefail

# Startup script to run the platform
# Checks for existing services and runs demo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "Pod Security Standards Platform Startup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [[ ! -d "${PROJECT_DIR}/services" ]]; then
    echo "Error: Project directory not found. Please run from project root."
    exit 1
fi

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if command -v curl &> /dev/null; then
        if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    # Check if process is running
    if pgrep -f "${service_name}" > /dev/null; then
        return 0
    fi
    
    return 1
}

# Check for duplicate services
echo "Checking for existing services..."
DUPLICATES=0

if check_service "log-ingestion" "8000"; then
    echo "⚠️  Warning: log-ingestion service already running on port 8000"
    DUPLICATES=$((DUPLICATES + 1))
fi

if check_service "log-processor" "8001"; then
    echo "⚠️  Warning: log-processor service already running on port 8001"
    DUPLICATES=$((DUPLICATES + 1))
fi

if check_service "log-query" "8002"; then
    echo "⚠️  Warning: log-query service already running on port 8002"
    DUPLICATES=$((DUPLICATES + 1))
fi

if [[ $DUPLICATES -gt 0 ]]; then
    echo ""
    echo "Found $DUPLICATES duplicate service(s)."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please stop existing services first."
        exit 1
    fi
fi

echo ""
echo "Starting services..."

# Start log-ingestion service
if ! check_service "log-ingestion" "8000"; then
    echo "Starting log-ingestion service..."
    cd "${PROJECT_DIR}/services/log-ingestion"
    if [[ -f "app.py" ]]; then
        "${PROJECT_DIR}/venv/bin/python3" -m uvicorn app:app --host 0.0.0.0 --port 8000 > /tmp/log-ingestion.log 2>&1 &
        INGESTION_PID=$!
        echo "  Started log-ingestion (PID: $INGESTION_PID)"
        sleep 2
    else
        echo "  Error: app.py not found"
    fi
else
    echo "  log-ingestion already running"
fi

# Start log-processor service
if ! check_service "log-processor" "8001"; then
    echo "Starting log-processor service..."
    cd "${PROJECT_DIR}/services/log-processor"
    if [[ -f "app.py" ]]; then
        "${PROJECT_DIR}/venv/bin/python3" -m uvicorn app:app --host 0.0.0.0 --port 8001 > /tmp/log-processor.log 2>&1 &
        PROCESSOR_PID=$!
        echo "  Started log-processor (PID: $PROCESSOR_PID)"
        sleep 2
    else
        echo "  Error: app.py not found"
    fi
else
    echo "  log-processor already running"
fi

# Start log-query service
if ! check_service "log-query" "8002"; then
    echo "Starting log-query service..."
    cd "${PROJECT_DIR}/services/log-query"
    if [[ -f "app.py" ]]; then
        "${PROJECT_DIR}/venv/bin/python3" -m uvicorn app:app --host 0.0.0.0 --port 8002 > /tmp/log-query.log 2>&1 &
        QUERY_PID=$!
        echo "  Started log-query (PID: $QUERY_PID)"
        sleep 2
    else
        echo "  Error: app.py not found"
    fi
else
    echo "  log-query already running"
fi

echo ""
echo "Waiting for services to be ready..."
sleep 3

# Verify services are running
echo ""
echo "Verifying services..."
ALL_READY=true

if check_service "log-ingestion" "8000"; then
    echo "✓ log-ingestion is ready"
else
    echo "✗ log-ingestion failed to start"
    ALL_READY=false
fi

if check_service "log-processor" "8001"; then
    echo "✓ log-processor is ready"
else
    echo "✗ log-processor failed to start"
    ALL_READY=false
fi

if check_service "log-query" "8002"; then
    echo "✓ log-query is ready"
else
    echo "✗ log-query failed to start"
    ALL_READY=false
fi

if [[ "$ALL_READY" == "false" ]]; then
    echo ""
    echo "Some services failed to start. Check logs:"
    echo "  tail -f /tmp/log-ingestion.log"
    echo "  tail -f /tmp/log-processor.log"
    echo "  tail -f /tmp/log-query.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "All services are running!"
echo "=========================================="
echo ""
echo "Service endpoints:"
echo "  - Log Ingestion:  http://localhost:8000"
echo "  - Log Processor:  http://localhost:8001"
echo "  - Log Query:      http://localhost:8002"
echo ""
echo "Run the demo script to generate metrics:"
echo "  ${SCRIPT_DIR}/demo.sh"
echo ""
echo "To stop services, run:"
echo "  pkill -f 'uvicorn app:app'"
echo ""

