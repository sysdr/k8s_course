#!/bin/bash
set -euo pipefail

echo "Getting dashboard URL..."

# Try to get NodePort
NODE_PORT=$(kubectl get svc frontend-service -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")

if [ -z "$NODE_PORT" ]; then
    echo "❌ Frontend service not found or not deployed yet."
    echo "   Deploy it first with: ./scripts/start-services.sh"
    exit 1
fi

# Try to get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || \
          kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null || \
          echo "localhost")

echo ""
echo "✅ Dashboard URL:"
echo "   http://${NODE_IP}:${NODE_PORT}"
echo ""
echo "   Or if accessing from localhost:"
echo "   http://localhost:${NODE_PORT}"
echo ""

