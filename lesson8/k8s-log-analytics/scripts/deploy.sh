#!/bin/bash
set -euo pipefail

echo "Deploying log analytics platform..."

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Apply base manifests
kubectl apply -f k8s/base/

# Apply Istio configuration
kubectl apply -f k8s/istio/

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s \
    deployment/log-ingestion -n log-analytics

kubectl wait --for=condition=available --timeout=300s \
    deployment/analytics-engine -n log-analytics

kubectl wait --for=condition=available --timeout=300s \
    deployment/dashboard -n log-analytics

echo "Deployment complete!"

# Check if port 8080 is already in use and kill existing port-forwards
echo "Checking for existing port-forwards on port 8080..."
if command -v lsof > /dev/null 2>&1; then
    EXISTING_PF=$(lsof -ti:8080 2>/dev/null || true)
    if [ -n "$EXISTING_PF" ]; then
        echo "Found existing process on port 8080, terminating..."
        kill $EXISTING_PF 2>/dev/null || true
        sleep 2
    fi
elif command -v netstat > /dev/null 2>&1; then
    EXISTING_PF=$(netstat -tlnp 2>/dev/null | grep ':8080 ' | awk '{print $7}' | cut -d'/' -f1 | head -1 || true)
    if [ -n "$EXISTING_PF" ]; then
        echo "Found existing process on port 8080, terminating..."
        kill $EXISTING_PF 2>/dev/null || true
        sleep 2
    fi
else
    echo "Note: Cannot check for existing processes (lsof/netstat not available)"
fi

# Verify dashboard service exists
echo "Verifying dashboard service..."
if ! kubectl get svc dashboard -n log-analytics > /dev/null 2>&1; then
    echo "Error: Dashboard service not found!"
    exit 1
fi

# Wait for service endpoints to be ready
echo "Waiting for dashboard endpoints..."
for i in {1..30}; do
    ENDPOINTS=$(kubectl get endpoints dashboard -n log-analytics -o jsonpath='{.subsets[0].addresses[*].ip}' 2>/dev/null || echo "")
    if [ -n "$ENDPOINTS" ]; then
        echo "Dashboard endpoints ready: $ENDPOINTS"
        break
    fi
    sleep 1
done

echo ""
echo "Starting port-forward..."
# Start port-forward in background with proper error handling
kubectl port-forward -n log-analytics svc/dashboard 8080:80 > /tmp/port-forward.log 2>&1 &
PORT_FORWARD_PID=$!

# Wait for port-forward to establish and verify it's working
echo "Waiting for port-forward to establish..."
PORT_READY=false
for i in {1..15}; do
    # Check if process is still running
    if ! kill -0 $PORT_FORWARD_PID 2>/dev/null; then
        echo "Error: Port-forward process died. Check logs:"
        cat /tmp/port-forward.log 2>/dev/null || echo "No log file found"
        exit 1
    fi
    
    # Try to verify port is listening (using netcat or curl if available)
    if command -v nc > /dev/null 2>&1; then
        if nc -z localhost 8080 2>/dev/null; then
            PORT_READY=true
            echo "Port-forward established successfully!"
            break
        fi
    elif command -v curl > /dev/null 2>&1; then
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            PORT_READY=true
            echo "Port-forward established successfully!"
            break
        fi
    elif command -v wget > /dev/null 2>&1; then
        if wget -q --spider http://localhost:8080 2>/dev/null; then
            PORT_READY=true
            echo "Port-forward established successfully!"
            break
        fi
    else
        # If no tools available, just wait and assume it's ready
        if [ $i -ge 5 ]; then
            PORT_READY=true
            echo "Port-forward started (assuming ready after wait period)"
            break
        fi
    fi
    sleep 1
done

# Final check if we have verification tools
if [ "$PORT_READY" = false ]; then
    if command -v nc > /dev/null 2>&1 || command -v curl > /dev/null 2>&1 || command -v wget > /dev/null 2>&1; then
        echo "Warning: Port-forward may not be working. Check logs:"
        cat /tmp/port-forward.log 2>/dev/null || echo "No log file found"
        echo ""
        echo "You can manually start port-forward with:"
        echo "  kubectl port-forward -n log-analytics svc/dashboard 8080:80"
        exit 1
    else
        echo "Note: Cannot verify port-forward (no verification tools available)"
        echo "Please check manually if http://localhost:8080 is accessible"
    fi
fi

# Open browser (works on Linux, macOS, and WSL)
echo "Opening dashboard in browser..."
sleep 1
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080 2>/dev/null &
elif command -v open > /dev/null; then
    open http://localhost:8080 2>/dev/null &
elif command -v start > /dev/null; then
    start http://localhost:8080 2>/dev/null &
else
    echo "Please open http://localhost:8080 in your browser"
fi

echo ""
echo "✓ Dashboard available at: http://localhost:8080"
echo "✓ Port-forward running in background (PID: $PORT_FORWARD_PID)"
echo "✓ To stop port-forward, run: kill $PORT_FORWARD_PID"
