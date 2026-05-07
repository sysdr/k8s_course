#!/usr/bin/env bash
# =============================================================================
# Lesson 65 — Docker cleanup (project root inside lesson65-dns-debug)
# Stops this lesson's Compose stacks, removes lesson containers/images,
# prunes unused Docker objects, optionally stops the Docker daemon.
#
# Usage:
#   ./cleanup.sh
#   STOP_DOCKER_DAEMON=1 ./cleanup.sh   # also try to stop Docker Engine (sudo)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LESSON_ROOT="${SCRIPT_DIR}"

info() { echo "[cleanup] $*"; }

info "Stopping Compose stacks (broken/ and fixed/)..."
for compose_dir in "${LESSON_ROOT}/broken" "${LESSON_ROOT}/fixed"; do
  if [[ -f "${compose_dir}/docker-compose.yml" ]]; then
    (cd "${compose_dir}" && docker compose down --remove-orphans --volumes 2>/dev/null) || true
  fi
done

info "Stopping containers named lesson65-* (any leftover)..."
for c in lesson65-api lesson65-processor; do
  docker rm -f "${c}" 2>/dev/null || true
done

info "Removing lesson-specific images (docker.io/library naming from compose builds)..."
while read -r img; do
  [[ -z "${img}" ]] && continue
  docker rmi -f "${img}" 2>/dev/null || true
done < <(
  docker images --format '{{.Repository}}:{{.Tag}}' |
    grep -E '^(broken|fixed)-(api-service|log-processor)(:latest)?$' ||
    true
)

info "Pruning unused Docker networks, containers, images, build cache, volumes (unused)..."
docker network rm lesson65-frontend lesson65-backend 2>/dev/null || true
set +e
docker container prune -f
docker image prune -af
docker builder prune -af
docker volume prune -f
docker network prune -f
set -e

if [[ "${STOP_DOCKER_DAEMON:-0}" == "1" ]]; then
  info "STOP_DOCKER_DAEMON=1 — attempting to stop Docker Engine (requires sufficient privileges)..."
  set +e
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop docker docker.socket 2>/dev/null
    sudo systemctl stop docker docker.socket 2>/dev/null
  elif command -v service >/dev/null 2>&1; then
    service docker stop 2>/dev/null
    sudo service docker stop 2>/dev/null
  else
    info "No systemctl/service found; skip Docker daemon stop."
  fi
  set -e
else
  info "Docker daemon left running (set STOP_DOCKER_DAEMON=1 to stop it)."
fi

info "Done."
