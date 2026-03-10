#!/bin/bash
set -euo pipefail
CLUSTER_NAME="${CLUSTER_NAME:-log-platform-local}"
echo "Tearing down cluster: $CLUSTER_NAME"
kind delete cluster --name "$CLUSTER_NAME"
echo "✅ Cluster deleted"
