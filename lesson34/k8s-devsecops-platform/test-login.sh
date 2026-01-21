#!/bin/bash

echo "=== Testing Login via Frontend Proxy ==="
echo ""

# Test login through nginx proxy
RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}')

echo "Response: $RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "access_token"; then
  echo "✓ Login successful via frontend proxy!"
else
  echo "✗ Login failed via frontend proxy"
  echo ""
  echo "Testing API Gateway directly:"
  curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"user","password":"user123"}' | head -3
fi
