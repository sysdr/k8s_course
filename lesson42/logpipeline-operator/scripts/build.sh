#!/bin/bash

set -euo pipefail

echo "Building Docker images..."

# Build operator image
docker build -t logpipeline/operator:latest ./operator/

# Build service images
docker build -t logpipeline/collector:latest ./services/log-collector/
docker build -t logpipeline/processor:latest ./services/log-processor/
docker build -t logpipeline/sink:latest ./services/log-sink/

# Build frontend image
docker build -t logpipeline/dashboard:latest ./frontend/

# Load images into kind cluster
kind load docker-image logpipeline/operator:latest --name logpipeline
kind load docker-image logpipeline/collector:latest --name logpipeline
kind load docker-image logpipeline/processor:latest --name logpipeline
kind load docker-image logpipeline/sink:latest --name logpipeline
kind load docker-image logpipeline/dashboard:latest --name logpipeline

echo "All images built and loaded successfully!"
