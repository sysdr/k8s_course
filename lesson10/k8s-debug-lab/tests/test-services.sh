#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

API_URL="${API_URL:-http://localhost:8002}"
INGESTER_URL="${INGESTER_URL:-http://localhost:8000}"
PROCESSOR_URL="${PROCESSOR_URL:-http://localhost:8001}"

echo "Running service tests..."
echo ""

FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo "✓ PASS"
        return 0
    else
        echo "✗ FAIL (got $status, expected $expected_status)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

test_json_response() {
    local name=$1
    local url=$2
    local field=$3
    
    echo -n "Testing $name ($field)... "
    response=$(curl -s "$url")
    
    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if '$field' in str(data) else 1)" 2>/dev/null; then
        value=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$field', 'N/A'))" 2>/dev/null)
        if [ "$value" != "0" ] && [ "$value" != "N/A" ] && [ -n "$value" ]; then
            echo "✓ PASS (value: $value)"
            return 0
        else
            echo "⚠ WARN (value is zero or missing: $value)"
            return 1
        fi
    else
        echo "✗ FAIL (invalid JSON or missing field)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test health endpoints
test_endpoint "Log Ingester Health" "${INGESTER_URL}/health"
test_endpoint "Log Processor Health" "${PROCESSOR_URL}/health"
test_endpoint "Log API Health" "${API_URL}/health"

# Test API endpoints
test_endpoint "Log API Summary" "${API_URL}/api/v1/summary"
test_endpoint "Log API Sources" "${API_URL}/api/v1/sources"
test_endpoint "Log API Logs" "${API_URL}/api/v1/logs?limit=10"

# Test metrics endpoints
test_endpoint "Log Ingester Metrics" "${INGESTER_URL}/metrics"
test_endpoint "Log Processor Metrics" "${PROCESSOR_URL}/metrics"
test_endpoint "Log API Metrics" "${API_URL}/metrics"

# Test that summary has non-zero values
echo ""
echo "Validating dashboard metrics..."
test_json_response "Total Logs" "${API_URL}/api/v1/summary" "total_logs"
test_json_response "Anomaly Count" "${API_URL}/api/v1/summary" "anomaly_count"

# Check by_level and by_source
summary=$(curl -s "${API_URL}/api/v1/summary")
if echo "$summary" | python3 -c "import sys, json; data=json.load(sys.stdin); by_level=data.get('by_level', {}); exit(0 if any(v > 0 for v in by_level.values()) else 1)" 2>/dev/null; then
    echo "✓ Logs by level has non-zero values"
else
    echo "⚠ Logs by level may have zero values"
    FAILED=$((FAILED + 1))
fi

if echo "$summary" | python3 -c "import sys, json; data=json.load(sys.stdin); by_source=data.get('by_source', {}); exit(0 if any(v > 0 for v in by_source.values()) else 1)" 2>/dev/null; then
    echo "✓ Logs by source has non-zero values"
else
    echo "⚠ Logs by source may have zero values"
    FAILED=$((FAILED + 1))
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ $FAILED test(s) failed"
    exit 1
fi
