#!/bin/bash

# Verify that the fixes are working

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="debug-challenge"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Verification Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Check pod status
echo -e "${YELLOW}Test 1: Pod Health${NC}"
FRONTEND_READY=$(kubectl get pods -n ${NAMESPACE} -l app=frontend -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
BACKEND_READY=$(kubectl get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')

if [ "$FRONTEND_READY" = "True" ]; then
  echo -e "  ${GREEN}✓${NC} Frontend pod is healthy"
else
  echo -e "  ${RED}✗${NC} Frontend pod is not ready"
fi

if [ "$BACKEND_READY" = "True" ]; then
  echo -e "  ${GREEN}✓${NC} Backend pod is healthy"
else
  echo -e "  ${RED}✗${NC} Backend pod is not ready"
fi

# Test 2: Service connectivity
echo ""
echo -e "${YELLOW}Test 2: Service Connectivity${NC}"
FRONTEND_POD=$(kubectl get pods -n ${NAMESPACE} -l app=frontend -o jsonpath='{.items[0].metadata.name}')

CURL_RESULT=$(kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- curl -s -o /dev/null -w "%{http_code}" http://backend-api:8000/health)
if [ "$CURL_RESULT" = "200" ]; then
  echo -e "  ${GREEN}✓${NC} Frontend can reach backend API"
else
  echo -e "  ${RED}✗${NC} Frontend cannot reach backend (HTTP $CURL_RESULT)"
fi

# Test 3: Data retrieval
echo ""
echo -e "${YELLOW}Test 3: Data Retrieval${NC}"
PRODUCTS=$(kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- curl -s http://backend-api:8000/api/products | grep -o '"id"' | wc -l)
if [ "$PRODUCTS" -gt 0 ]; then
  echo -e "  ${GREEN}✓${NC} Backend returning product data ($PRODUCTS products)"
else
  echo -e "  ${RED}✗${NC} Backend not returning data"
fi

# Test 4: Frontend public access
echo ""
echo -e "${YELLOW}Test 4: External Access${NC}"
echo "Getting frontend service URL..."
kubectl get svc frontend-svc -n ${NAMESPACE}

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verification complete!${NC}"
echo ""
echo "Access the application:"
echo "  kubectl port-forward -n debug-challenge svc/frontend-svc 8080:80"
echo "  Then visit: http://localhost:8080"
echo -e "${BLUE}========================================${NC}"
