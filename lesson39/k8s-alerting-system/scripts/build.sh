#!/bin/bash
set -e
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "Pre-pulling base images..."
docker pull python:3.11-slim &
docker pull node:18-alpine &
docker pull nginx:alpine &
wait
echo "✓ Base images pre-pulled"

echo "Building images in parallel..."
docker build -t log-ingestor:latest microservices/log-ingestor &
PID1=$!
docker build -t log-transformer:latest microservices/log-transformer &
PID2=$!
docker build -t log-analyzer:latest microservices/log-analyzer &
PID3=$!

wait $PID1 $PID2 $PID3
echo "✓ All images built"
