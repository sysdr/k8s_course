#!/bin/bash
set -euo pipefail

echo "Cleaning up clusters..."

kind delete cluster --name cluster-a
kind delete cluster --name cluster-b

echo "Cleanup complete!"
