#!/bin/bash
# =============================================================================
# diagnose.sh — DNS Debugging Toolkit for Lesson 65
# Run this from inside the broken/ or fixed/ directory context.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_CONTAINER="lesson65-api"
PROCESSOR_CONTAINER="lesson65-processor"

print_section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE} $1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_container_running() {
  local name="$1"
  if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
    echo -e "${GREEN}✓ ${name} is running${NC}"
    return 0
  else
    echo -e "${RED}✗ ${name} is NOT running${NC}"
    return 1
  fi
}

# 1. Container status
print_section "1. Container Status"
check_container_running "${API_CONTAINER}"      || true
check_container_running "${PROCESSOR_CONTAINER}" || true

# 2. Network membership
print_section "2. Network Membership"
echo "API Service networks:"
docker inspect "${API_CONTAINER}" \
  --format '{{range $net, $cfg := .NetworkSettings.Networks}}  - {{$net}} (IP: {{$cfg.IPAddress}}){{printf "\n"}}{{end}}' \
  2>/dev/null || echo -e "${RED}  Cannot inspect ${API_CONTAINER}${NC}"

echo ""
echo "Log Processor networks:"
docker inspect "${PROCESSOR_CONTAINER}" \
  --format '{{range $net, $cfg := .NetworkSettings.Networks}}  - {{$net}} (IP: {{$cfg.IPAddress}}){{printf "\n"}}{{end}}' \
  2>/dev/null || echo -e "${RED}  Cannot inspect ${PROCESSOR_CONTAINER}${NC}"

# 3. DNS resolver config inside api-service
print_section "3. DNS Resolver Config (inside api-service)"
docker exec "${API_CONTAINER}" cat /etc/resolv.conf 2>/dev/null \
  || echo -e "${RED}  Cannot exec into ${API_CONTAINER}${NC}"

# 4. DNS resolution attempts
print_section "4. DNS Resolution Tests (from api-service)"

echo -e "${YELLOW}Testing: nslookup log-processor${NC}"
docker exec "${API_CONTAINER}" nslookup log-processor 127.0.0.11 2>&1 || true

echo ""
echo -e "${YELLOW}Testing: nslookup processor (alias)${NC}"
docker exec "${API_CONTAINER}" nslookup processor 127.0.0.11 2>&1 || true

echo ""
echo -e "${YELLOW}Testing: nslookup log-svc (alias)${NC}"
docker exec "${API_CONTAINER}" nslookup log-svc 127.0.0.11 2>&1 || true

# 5. HTTP connectivity test
print_section "5. HTTP Connectivity Test"
echo -e "${YELLOW}Attempting HTTP GET http://processor:8080/health from api-service${NC}"
docker exec "${API_CONTAINER}" \
  wget -qO- --timeout=5 "http://processor:8080/health" 2>&1 \
  && echo -e "\n${GREEN}✓ HTTP connectivity confirmed${NC}" \
  || echo -e "${RED}✗ HTTP connection failed${NC}"

# 6. API health endpoint
print_section "6. API Service Self-Report"
curl -sf http://localhost:8000/health 2>/dev/null | python3 -m json.tool \
  || echo -e "${RED}  API health endpoint not reachable${NC}"

echo ""
echo "Diagnosis complete. Review NXDOMAIN vs 'connection refused' vs timeout carefully."
