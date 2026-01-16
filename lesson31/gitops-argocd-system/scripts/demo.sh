#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "============================================"
echo "GitOps Platform Demo Script"
echo "============================================"
echo ""
echo "This script generates test data to demonstrate the dashboard"
echo ""

# Check if event processor is accessible
EVENTS_API="${EVENTS_API:-http://localhost:8001}"

echo "Checking if event processor is running..."
if ! curl -s "${EVENTS_API}/health" &> /dev/null; then
    echo "⚠️  Event processor not accessible at ${EVENTS_API}"
    echo "   Please ensure the service is running and port-forward is active:"
    echo "   kubectl port-forward svc/event-processor -n gitops-apps-prod 8001:8001"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Generating test deployment events..."
echo ""

# Generate test events
for i in {1..5}; do
    APP_NAME="gitops-platform-prod"
    EVENT_TYPE="sync-succeeded"
    SYNC_STATUS="Synced"
    HEALTH_STATUS="Healthy"
    
    if [ $i -eq 3 ]; then
        EVENT_TYPE="sync-failed"
        SYNC_STATUS="OutOfSync"
        HEALTH_STATUS="Degraded"
    fi
    
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    REVISION="main-$(date +%s)-$i"
    
    EVENT_PAYLOAD=$(cat <<EOF
{
  "metadata": {
    "name": "${APP_NAME}",
    "namespace": "gitops-apps-prod"
  },
  "status": {
    "sync": {
      "status": "${SYNC_STATUS}",
      "revision": "${REVISION}"
    },
    "health": {
      "status": "${HEALTH_STATUS}"
    }
  },
  "type": "${EVENT_TYPE}",
  "message": "Demo deployment event ${i}"
}
EOF
)
    
    echo "Sending event ${i}..."
    curl -s -X POST "${EVENTS_API}/webhook/argocd" \
        -H "Content-Type: application/json" \
        -d "${EVENT_PAYLOAD}" > /dev/null || echo "  ⚠️  Failed to send event ${i}"
    
    sleep 1
done

echo ""
echo "Waiting for events to be processed..."
sleep 2

echo ""
echo "Fetching statistics..."
STATS=$(curl -s "${EVENTS_API}/api/stats" || echo '{}')

echo ""
echo "Current Statistics:"
echo "==================="
echo "${STATS}" | python3 -m json.tool 2>/dev/null || echo "${STATS}"
echo ""

# Check if stats are non-zero
TOTAL_DEPLOYMENTS=$(echo "${STATS}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_deployments', 0))" 2>/dev/null || echo "0")

if [ "${TOTAL_DEPLOYMENTS}" -gt 0 ]; then
    echo "✅ Success! Dashboard should now show non-zero values"
    echo ""
    echo "Access the dashboard:"
    echo "  kubectl port-forward svc/dashboard -n gitops-apps-prod 8081:80"
    echo "  Then open: http://localhost:8081"
else
    echo "⚠️  Warning: Statistics still show zero values"
    echo "   This may indicate:"
    echo "   - Event processor database not initialized"
    echo "   - Events not being processed"
    echo "   - Service connectivity issues"
fi

echo ""
echo "============================================"
