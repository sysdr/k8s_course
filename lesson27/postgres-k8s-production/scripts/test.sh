#!/bin/bash
set -euo pipefail

echo "Running integration tests..."

# Wait for all services to be ready
kubectl wait --for=condition=ready pod -l app=database-api -n services --timeout=180s

# Get API endpoint
API_POD=$(kubectl get pod -n services -l app=database-api -o jsonpath='{.items[0].metadata.name}')

# Test health endpoint
echo "Testing health endpoint..."
kubectl exec -n services $API_POD -- curl -f http://localhost:8000/health

# Test user creation
echo "Testing user creation..."
kubectl exec -n services $API_POD -- curl -f -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com"}'

# Test user listing
echo "Testing user listing..."
kubectl exec -n services $API_POD -- curl -f http://localhost:8000/users

# Test database stats
echo "Testing database stats..."
kubectl exec -n services $API_POD -- curl -f http://localhost:8000/stats/database

echo "All tests passed!"
