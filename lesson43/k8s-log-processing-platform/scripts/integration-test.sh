#!/bin/bash
# Integration tests: health checks and API smoke tests.
# Set API_BASE (default http://localhost:8000 for ingestion, http://localhost:8002 for analytics)
set -euo pipefail

INGEST_URL="${INGEST_URL:-http://localhost:8000}"
ANALYTICS_URL="${ANALYTICS_URL:-http://localhost:8002}"
FAIL=0

check() { if [ $? -eq 0 ]; then echo "  ✓ $1"; else echo "  ✗ $1"; FAIL=1; fi; }

echo "🧪 Integration tests..."
echo "  Ingestion: $INGEST_URL | Analytics: $ANALYTICS_URL"

curl -sf "$INGEST_URL/health" > /dev/null; check "log-ingestion health"
curl -sf "$ANALYTICS_URL/health" > /dev/null; check "analytics-api health"
curl -sf "$ANALYTICS_URL/api/v1/analytics/summary" | grep -q "summaries"; check "analytics summary"

if [ $FAIL -eq 0 ]; then echo "✅ All integration tests passed."; else echo "❌ Some tests failed."; exit 1; fi
