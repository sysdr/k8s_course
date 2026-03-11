#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PORTAL_PUBLIC="$PROJECT_ROOT/platform-portal/public"
cd "$PORTAL_PUBLIC"
if command -v npx >/dev/null 2>&1; then
  exec npx --yes serve . -l 3000
else
  exec python3 -m http.server 3000
fi
