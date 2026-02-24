#!/bin/bash
# Stop containers and remove unused Docker resources.
# Also removes node_modules, venv, .pytest_cache, .pyc, and Istio generated/cache artifacts from this project.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Stopping services ==="
# Delete Kind clusters
for name in $(kind get clusters 2>/dev/null || true); do
  echo "Deleting Kind cluster: $name"
  kind delete cluster --name "$name" 2>/dev/null || true
done

# Stop Docker containers (if Docker is running)
if command -v docker &>/dev/null; then
  RUNNING=$(docker ps -q 2>/dev/null || true)
  if [[ -n "$RUNNING" ]]; then
    echo "Stopping Docker containers..."
    docker stop $RUNNING 2>/dev/null || true
  fi
  echo "Removing stopped containers..."
  docker container prune -f 2>/dev/null || true
  echo "Removing unused images..."
  docker image prune -af 2>/dev/null || true
  echo "Removing unused networks..."
  docker network prune -f 2>/dev/null || true
  echo "Removing build cache..."
  docker builder prune -af 2>/dev/null || true
  echo "Docker cleanup done."
else
  echo "Docker not found, skipping container cleanup."
fi

echo ""
echo "=== Removing project artifacts (node_modules, venv, .pytest_cache, .pyc, Istio cache) ==="
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name "node_modules" -print0 2>/dev/null) || true
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name "venv" -print0 2>/dev/null) || true
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name ".venv" -print0 2>/dev/null) || true
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name ".pytest_cache" -print0 2>/dev/null) || true
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name "__pycache__" -print0 2>/dev/null) || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
while IFS= read -r -d '' d; do rm -rf "$d"; done < <(find . -type d -name ".istio" -print0 2>/dev/null) || true
find . -type f \( -name "*.istio.yaml" -o -name "*.istio.yml" \) -delete 2>/dev/null || true
echo "Artifact cleanup done."

echo ""
echo "=== Cleanup complete ==="
