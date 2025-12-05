#!/bin/bash

set -euo pipefail

echo "🧹 Cleaning up debugging challenge..."

kubectl delete namespace debugging-challenge --ignore-not-found=true

echo "✅ Cleanup complete!"
