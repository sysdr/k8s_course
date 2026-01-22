#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Starting Services Locally ==="
echo "Project root: $PROJECT_ROOT"

# Check if services are already running
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "Port $port is already in use"
        return 1
    fi
    return 0
}

# Check for duplicate services
echo "Checking for existing services..."
if ! check_port 8000; then
    echo "ERROR: Order service is already running on port 8000"
    exit 1
fi

if ! check_port 8001; then
    echo "ERROR: Payment service is already running on port 8001"
    exit 1
fi

if ! check_port 3000; then
    echo "WARNING: Port 3000 is in use (may be frontend or another service)"
fi

# Start Order Service
echo "Starting Order Service on port 8000..."
cd "$PROJECT_ROOT/services/order-service"

# Try to use venv, fallback to system Python
USE_VENV=false
if [ ! -d "venv" ]; then
    if python3 -m venv venv 2>/dev/null; then
        echo "Created virtual environment"
        USE_VENV=true
    else
        echo "Warning: Could not create venv, using system Python"
    fi
else
    USE_VENV=true
fi

if [ "$USE_VENV" = true ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PIP_CMD="pip"
else
    PIP_CMD="pip3"
fi

# Install dependencies
$PIP_CMD install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true

# Start service
if [ "$USE_VENV" = true ] && [ -f "venv/bin/activate" ]; then
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/order-service.log 2>&1 &
else
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/order-service.log 2>&1 &
fi
ORDER_PID=$!
echo "Order Service started (PID: $ORDER_PID)"

# Start Payment Service
echo "Starting Payment Service on port 8001..."
cd "$PROJECT_ROOT/services/payment-service"
if [ ! -f "payment-service" ]; then
    echo "Building payment service..."
    go mod download
    go build -o payment-service ./cmd
fi
./payment-service > /tmp/payment-service.log 2>&1 &
PAYMENT_PID=$!
echo "Payment Service started (PID: $PAYMENT_PID)"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 3

# Check if services are running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "ERROR: Order service failed to start"
    cat /tmp/order-service.log
    exit 1
fi

if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "ERROR: Payment service failed to start"
    cat /tmp/payment-service.log
    exit 1
fi

echo ""
echo "=== Services Started Successfully ==="
echo "Order Service: http://localhost:8000"
echo "Payment Service: http://localhost:8001"
echo ""
echo "PIDs: Order=$ORDER_PID, Payment=$PAYMENT_PID"
echo "Logs: /tmp/order-service.log, /tmp/payment-service.log"
echo ""
echo "To stop services, run: kill $ORDER_PID $PAYMENT_PID"
echo "Or use: ./scripts/deployment/stop-services.sh"

# Save PIDs to file for easy cleanup
echo "$ORDER_PID $PAYMENT_PID" > /tmp/ecommerce-service-pids.txt
