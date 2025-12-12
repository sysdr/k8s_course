#!/bin/bash
set -euo pipefail

echo "Testing Pod Security Standards enforcement..."
echo ""

# Test 1: Try to deploy privileged pod in baseline namespace (should fail)
echo "Test 1: Attempting to deploy privileged pod in logs-public (baseline)..."
cat <<EOF | kubectl apply -f - 2>&1 | tee /tmp/test1.log || true
apiVersion: v1
kind: Pod
metadata:
  name: test-privileged
  namespace: logs-public
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      privileged: true
