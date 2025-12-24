#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running threat simulations..."

POD=$(kubectl get pod -n runtime-security -l app=threat-simulator -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD" ]; then
    echo "Error: Threat simulator pod not found"
    exit 1
fi

echo "→ Simulating shell spawn..."
kubectl exec -n runtime-security "$POD" -- python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/simulate/shell-spawn', data=b'')"

sleep 2

echo "→ Simulating file access..."
kubectl exec -n runtime-security "$POD" -- python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/simulate/sensitive-file', data=b'')"

echo "✓ Threat simulations complete. Check dashboard for events."
