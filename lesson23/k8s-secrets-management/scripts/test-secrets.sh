#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Testing Secrets Management from: $PROJECT_ROOT"

NAMESPACE="secrets-platform"

# Test 1: Check if secrets are mounted correctly
echo "Test 1: Verifying secret mounts..."
kubectl exec -n $NAMESPACE deployment/log-ingestion-service -- \
    ls -la /var/run/secrets/api-keys/

# Test 2: Test API key rotation detection
echo "Test 2: Testing secret rotation..."
kubectl get secret ingestion-api-keys -n $NAMESPACE -o json | \
    jq '.data["api-keys"]' -r | base64 -d

# Test 3: Check service health with secrets loaded
echo "Test 3: Checking service health..."
kubectl exec -n $NAMESPACE deployment/log-ingestion-service -- \
    curl -s http://localhost:8080/health | jq .

# Test 4: Verify rotation service is working
echo "Test 4: Checking rotation status..."
kubectl exec -n $NAMESPACE deployment/secrets-rotation-service -- \
    curl -s http://localhost:8080/api/v1/rotation/status | jq .

echo "All tests completed!"
