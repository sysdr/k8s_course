#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Cleaning up multi-cluster environment..."

kind delete cluster --name control-plane
kind delete cluster --name cluster-us-west
kind delete cluster --name cluster-eu-west
kind delete cluster --name cluster-ap-southeast

echo "Cleanup complete!"
