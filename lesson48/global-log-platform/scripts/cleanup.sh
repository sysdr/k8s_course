#!/bin/bash
# cleanup.sh — Teardown all resources
set -euo pipefail
echo "WARNING: This will delete both kind clusters and all data."
read -r -p "Confirm (yes/no): " confirm
[[ "$confirm" == "yes" ]] || { echo "Aborted."; exit 0; }
kind delete cluster --name us-east 2>/dev/null || true
kind delete cluster --name eu-west 2>/dev/null || true
echo "✓ Clusters deleted"
