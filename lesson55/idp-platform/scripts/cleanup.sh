#!/bin/bash

set -euo pipefail

echo "=== Cleaning up IDP Platform ==="

read -p "This will delete the entire cluster. Are you sure? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

kind delete cluster --name idp-platform

echo "✓ Cluster deleted successfully!"
