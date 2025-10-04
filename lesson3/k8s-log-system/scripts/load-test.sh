#!/bin/bash
set -euo pipefail

echo "Running load test..."

# Get frontend service endpoint
FRONTEND_URL=$(kubectl get svc frontend -n log-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$FRONTEND_URL" ]; then
    echo "LoadBalancer IP not available. Using port-forward instead."
    kubectl port-forward -n log-system svc/frontend 8080:80 &
    PORTFORWARD_PID=$!
    sleep 5
    FRONTEND_URL="localhost:8080"
fi

# Run load test
for i in {1..1000}; do
    curl -s "http://${FRONTEND_URL}/api/stats" > /dev/null &
    if [ $((i % 100)) -eq 0 ]; then
        echo "Sent $i requests..."
    fi
done

wait
echo "Load test complete!"

if [ ! -z "$PORTFORWARD_PID" ]; then
    kill $PORTFORWARD_PID
fi
