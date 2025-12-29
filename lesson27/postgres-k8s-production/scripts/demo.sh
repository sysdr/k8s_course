#!/bin/bash
set -euo pipefail

echo "Running demo to generate data for dashboard..."

# Wait for API to be ready
echo "Waiting for database-api to be ready..."
kubectl wait --for=condition=ready pod -l app=database-api -n services --timeout=180s || true

# Get API service endpoint
API_SERVICE=$(kubectl get svc database-api -n services -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
API_POD=$(kubectl get pod -n services -l app=database-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$API_POD" ]; then
    echo "ERROR: database-api pod not found"
    exit 1
fi

echo "Generating demo users..."
# Generate multiple users
for i in {1..20}; do
    kubectl exec -n services $API_POD -- curl -s -X POST http://localhost:8000/users \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"demo_user_${i}\",\"email\":\"user${i}@demo.com\"}" > /dev/null 2>&1 || true
    echo "Created user ${i}/20"
    sleep 0.5
done

echo "Generating query statistics..."
# Make multiple API calls to generate query stats
for i in {1..30}; do
    kubectl exec -n services $API_POD -- curl -s http://localhost:8000/users > /dev/null 2>&1 || true
    kubectl exec -n services $API_POD -- curl -s http://localhost:8000/stats/database > /dev/null 2>&1 || true
    if [ $((i % 5)) -eq 0 ]; then
        echo "Generated ${i}/30 queries"
    fi
    sleep 0.3
done

echo "Demo data generation complete!"
echo ""
echo "Dashboard should now show:"
echo "  - Multiple users in the Recent Users section"
echo "  - Non-zero database size"
echo "  - Active connections > 0"
echo "  - Query statistics with data"
echo ""
echo "Access dashboard: kubectl port-forward -n services svc/frontend 8080:80"

