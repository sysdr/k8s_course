#!/bin/bash
set -euo pipefail

echo "Fixing dashboard port-forward..."

# Kill any existing port-forwards on 8080
echo "Checking for existing processes on port 8080..."
if command -v lsof > /dev/null 2>&1; then
    EXISTING_PF=$(lsof -ti:8080 2>/dev/null || true)
    if [ -n "$EXISTING_PF" ]; then
        echo "Killing existing process on port 8080 (PID: $EXISTING_PF)..."
        kill $EXISTING_PF 2>/dev/null || true
        sleep 2
    fi
elif command -v netstat > /dev/null 2>&1; then
    EXISTING_PF=$(netstat -tlnp 2>/dev/null | grep ':8080 ' | awk '{print $7}' | cut -d'/' -f1 | head -1 || true)
    if [ -n "$EXISTING_PF" ]; then
        echo "Killing existing process on port 8080 (PID: $EXISTING_PF)..."
        kill $EXISTING_PF 2>/dev/null || true
        sleep 2
    fi
fi

# Check if dashboard service exists
if ! kubectl get svc dashboard -n log-analytics > /dev/null 2>&1; then
    echo "Error: Dashboard service not found in namespace log-analytics"
    echo "Please run ./scripts/deploy.sh first"
    exit 1
fi

# Check if dashboard pods are ready
echo "Checking dashboard pods..."
PODS_READY=$(kubectl get pods -n log-analytics -l app=dashboard -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -c "True" || echo "0")
if [ "$PODS_READY" -eq "0" ]; then
    echo "Warning: No dashboard pods are ready. Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=dashboard -n log-analytics --timeout=60s || {
        echo "Error: Dashboard pods are not ready"
        echo "Check pod status with: kubectl get pods -n log-analytics"
        exit 1
    }
fi

# Wait for endpoints
echo "Waiting for dashboard endpoints..."
for i in {1..30}; do
    ENDPOINTS=$(kubectl get endpoints dashboard -n log-analytics -o jsonpath='{.subsets[0].addresses[*].ip}' 2>/dev/null || echo "")
    if [ -n "$ENDPOINTS" ]; then
        echo "Dashboard endpoints ready: $ENDPOINTS"
        break
    fi
    sleep 1
done

# Start port-forward
echo ""
echo "Starting port-forward..."
kubectl port-forward -n log-analytics svc/dashboard 8080:80 &
PORT_FORWARD_PID=$!

# Wait and verify
echo "Waiting for port-forward to establish..."
sleep 3

if kill -0 $PORT_FORWARD_PID 2>/dev/null; then
    # Test connection
    if command -v curl > /dev/null 2>&1; then
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            echo "✓ Port-forward is working!"
        else
            echo "⚠ Port-forward started but connection test failed"
            echo "  Try accessing http://localhost:8080 manually"
        fi
    elif command -v nc > /dev/null 2>&1; then
        if nc -z localhost 8080 2>/dev/null; then
            echo "✓ Port-forward is working!"
        else
            echo "⚠ Port-forward started but connection test failed"
            echo "  Try accessing http://localhost:8080 manually"
        fi
    else
        echo "✓ Port-forward started (PID: $PORT_FORWARD_PID)"
        echo "  Please test http://localhost:8080 manually"
    fi
    
    echo ""
    echo "Dashboard should be available at: http://localhost:8080"
    echo "Port-forward PID: $PORT_FORWARD_PID"
    echo "To stop: kill $PORT_FORWARD_PID"
    
    # Try to open browser
    sleep 1
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:8080 2>/dev/null &
    elif command -v open > /dev/null; then
        open http://localhost:8080 2>/dev/null &
    fi
else
    echo "Error: Port-forward process failed to start"
    exit 1
fi


