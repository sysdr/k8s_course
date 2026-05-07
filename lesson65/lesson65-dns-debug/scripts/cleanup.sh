#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "Cleaning up all Lesson 65 containers and networks..."

cd "${PROJECT_ROOT}/broken"
docker compose down --remove-orphans --volumes 2>/dev/null || true

cd "${PROJECT_ROOT}/fixed"
docker compose down --remove-orphans --volumes 2>/dev/null || true

docker network rm lesson65-frontend lesson65-backend 2>/dev/null || true

echo "Cleanup complete."
