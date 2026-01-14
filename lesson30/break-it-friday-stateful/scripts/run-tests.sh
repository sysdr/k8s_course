#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Break-It-Friday Test Suite${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

API_URL="${API_URL:-http://localhost:8000}"
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "Testing ${description}... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}${endpoint}" || echo "000")
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL (HTTP ${HTTP_CODE}, expected ${expected_status})${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_health_data() {
    local service=$1
    local field=$2
    
    echo -n "Testing ${service} ${field} is not zero... "
    
    HEALTH_DATA=$(curl -s "${API_URL}/health/all" || echo "{}")
    
    if [ "$HEALTH_DATA" = "{}" ]; then
        echo -e "${RED}✗ FAIL (No data returned)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Extract value using Python for JSON parsing
    VALUE=$(echo "$HEALTH_DATA" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    service_data = data.get('services', {}).get('${service}', {})
    value = service_data.get('${field}', 0)
    print(value)
except:
    print('0')
" 2>/dev/null || echo "0")
    
    if [ "$VALUE" != "0" ] && [ -n "$VALUE" ] && [ "$VALUE" != "null" ]; then
        echo -e "${GREEN}✓ PASS (${field}=${VALUE})${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL (${field}=${VALUE}, expected non-zero${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if API is accessible
echo -e "${YELLOW}Checking API availability...${NC}"
if ! curl -s -f "${API_URL}/health" > /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to API at ${API_URL}${NC}"
    echo "Start the services first: ./start-services.sh"
    exit 1
fi
echo -e "${GREEN}✓ API is accessible${NC}"
echo ""

# Run tests
echo -e "${YELLOW}Running API tests...${NC}"
echo ""

test_endpoint "/" "Root endpoint"
test_endpoint "/health" "Health check endpoint"
test_endpoint "/health/postgres" "PostgreSQL health check" 200
test_endpoint "/health/redis" "Redis health check" 200
test_endpoint "/health/all" "All services health check"

echo ""
echo -e "${YELLOW}Testing metrics are non-zero...${NC}"
echo ""

# Test that metrics are updating (not zero)
test_health_data "postgresql" "latency_ms"
test_health_data "redis" "latency_ms"

# Test overall status
echo -n "Testing overall status is not empty... "
OVERALL_STATUS=$(curl -s "${API_URL}/health/all" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('overall_status', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -n "$OVERALL_STATUS" ] && [ "$OVERALL_STATUS" != "null" ]; then
    echo -e "${GREEN}✓ PASS (status=${OVERALL_STATUS})${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL (status is empty)${NC}"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "Test Summary:"
echo -e "  ${GREEN}Passed: ${TESTS_PASSED}${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: ${TESTS_FAILED}${NC}"
    exit 1
else
    echo -e "  ${GREEN}Failed: ${TESTS_FAILED}${NC}"
    exit 0
fi
