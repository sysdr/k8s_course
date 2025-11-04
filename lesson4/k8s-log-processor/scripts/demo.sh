#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }

# Get ingestion pod to exec from
INGESTION_POD=$(kubectl get pod -n log-processor -l app=log-ingestion -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$INGESTION_POD" ]; then
    log_error "Ingestion pod not found"
    exit 1
fi

log_info "Sending demo log entries..."

# Use Python to send requests from within the cluster
for i in {1..20}; do
    kubectl exec -n log-processor "$INGESTION_POD" -- python3 -c "
import urllib.request
import json
import sys

data = {
    'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'level': 'INFO',
    'message': 'Demo log entry $i',
    'source': 'demo-script'
}

req = urllib.request.Request('http://log-ingestion-service/ingest',
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(req)
except Exception as e:
    pass
" 2>/dev/null || true
    sleep 0.5
done

log_info "Demo logs sent!"
