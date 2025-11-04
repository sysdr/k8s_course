#!/bin/bash
set -e
cd "$(dirname "$0")/.."
docker build -t log-ingestion:latest apps/log-ingestion/
docker build -t log-analytics:latest apps/log-analytics/
docker build -t dashboard:latest apps/dashboard/
echo "Build complete"
