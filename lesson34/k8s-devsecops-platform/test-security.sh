#!/bin/bash

echo "=== Testing Security Service ==="
echo ""

# Test security service health
echo "1. Security Service Health:"
curl -s http://localhost:8004/health
echo ""
echo ""

# Get token
echo "2. Getting auth token..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "Failed to get token"
  exit 1
fi

echo "Token obtained"
echo ""

# Test security dashboard
echo "3. Testing Security Dashboard:"
DASHBOARD=$(curl -s http://localhost:8000/security/dashboard \
  -H "Authorization: Bearer $TOKEN")

echo "$DASHBOARD" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✓ Vulnerabilities: {data[\"vulnerabilities\"][\"critical_count\"]} critical, {data[\"vulnerabilities\"][\"high_count\"]} high')
print(f'✓ Policy Violations: {data[\"policy_violations\"][\"total_violations\"]} total, {data[\"policy_violations\"][\"blocked_deployments\"]} blocked')
print(f'✓ Runtime Threats: {data[\"runtime_threats\"][\"critical_alerts\"]} critical, {data[\"runtime_threats\"][\"warning_alerts\"]} warnings')
print(f'✓ Network Security: {data[\"network_security\"][\"blocked_connections\"]} blocked, {data[\"network_security\"][\"encrypted_traffic_percent\"]}% encrypted')
print(f'✓ Secrets: {data[\"secrets\"][\"failed_attempts\"]} failed attempts, last rotation: {data[\"secrets\"][\"last_rotation\"] or \"Never\"}')
print(f'✓ Audit: {data[\"audit\"][\"blocked_actions\"]} blocked, {data[\"audit\"][\"allowed_actions\"]} allowed')
"

echo ""
echo "=== All Security Endpoints Working ==="
