#!/bin/bash
set -euo pipefail

echo "Building images..."
docker build -t log-ingestion-api:latest services/log-ingestion-api/
docker build -t log-processor-worker:latest services/log-processor-worker/
docker build -t analytics-dashboard:latest services/analytics-dashboard/

kind load docker-image log-ingestion-api:latest --name log-processing
kind load docker-image log-processor-worker:latest --name log-processing
kind load docker-image analytics-dashboard:latest --name log-processing

echo "Build complete!"
