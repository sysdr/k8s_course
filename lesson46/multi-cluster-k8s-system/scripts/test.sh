#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

FAIL=0
BASE_URL="${TEST_BASE_URL:-http://localhost:30080}"

test_curl() {
  local name="$1" url="$2"
  if curl -sf --connect-timeout 3 "$url" > /dev/null; then
    echo "PASS: $name"
  else
    echo "FAIL: $name ($url)"
    FAIL=1
  fi
}

echo "Running smoke tests (TEST_BASE_URL=$BASE_URL)..."
test_curl "Dashboard root" "$BASE_URL/"
if curl -sf --connect-timeout 3 "$BASE_URL/health" > /dev/null 2>&1; then
  echo "PASS: Health/readiness"
else
  echo "SKIP: Health/readiness (optional)"
fi
echo "Tests finished. Exit code: $FAIL"
exit $FAIL
