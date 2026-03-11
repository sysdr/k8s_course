#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_URL="${API_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-demo-token}"
echo "=== Running IDP demo against $API_URL ==="
curl -s -X GET "$API_URL/health" | head -1
curl -s -X POST "$API_URL/api/v1/teams" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"team_name":"demo-team","quota_tier":"default"}' | head -1
curl -s -X GET "$API_URL/api/v1/platform/stats" -H "Authorization: Bearer $TOKEN" | head -1
curl -s -X GET "$API_URL/metrics" | grep -E "platform_|#" | head -20
echo "=== Demo complete. Dashboard metrics should be updated. ==="
