#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Building Docker images..."

cd "${BASE_DIR}/services/security-event-processor"
docker build -t security-event-processor:latest .

cd "${BASE_DIR}/services/incident-response-controller"
docker build -t incident-response-controller:latest .

cd "${BASE_DIR}/services/threat-simulator"
docker build -t threat-simulator:latest .

cd "${BASE_DIR}/frontend"
docker build -t security-dashboard:latest .

echo "✓ All images built successfully"
