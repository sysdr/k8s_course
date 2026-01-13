#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Running demo to generate log events..."

PRODUCER_POD=$(kubectl get pods -n kafka-pipeline -l app=producer -o jsonpath='{.items[0].metadata.name}')

if [ -z "$PRODUCER_POD" ]; then
    echo "Error: Producer pod not found"
    exit 1
fi

# Generate sample log events
for i in {1..50}; do
    kubectl exec -n kafka-pipeline "$PRODUCER_POD" -- python -c "
import requests
import json
from datetime import datetime

data = {
    'service': 'web-app',
    'level': ['INFO', 'WARNING', 'ERROR'][$i % 3],
    'message': f'Demo log event number $i',
    'timestamp': datetime.utcnow().isoformat()
}

response = requests.post('http://localhost:8000/produce', json=data)
print(f'Event $i: {response.status_code}')
" || true
    sleep 0.5
done

echo "Demo completed. Check dashboard for metrics."
