#!/bin/bash

# Apply fixes to the broken application

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="debug-challenge"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Applying Fixes${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Select which fix to apply:${NC}"
echo "1) Fix service name mismatch (rename service)"
echo "2) Fix frontend environment variable"
echo "3) Apply correct network policies"
echo "4) Apply all fixes"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
  1)
    echo -e "${GREEN}Applying service name fix...${NC}"
    echo "Deleting incorrect service..."
    kubectl delete svc backend-api -n ${NAMESPACE} 2>/dev/null || true
    echo "Creating correct service..."
    kubectl apply -f k8s/fixed/backend.yaml
    echo -e "${GREEN}Service fix applied!${NC}"
    ;;
  2)
    echo -e "${GREEN}Updating frontend environment variable...${NC}"
    kubectl apply -f k8s/fixed/frontend.yaml
    echo -e "${GREEN}Frontend fix applied!${NC}"
    ;;
  3)
    echo -e "${GREEN}Applying network policies...${NC}"
    kubectl apply -f k8s/fixed/network-policy.yaml
    echo -e "${GREEN}Network policies applied!${NC}"
    ;;
  4)
    echo -e "${GREEN}Applying all fixes...${NC}"
    kubectl delete svc backend-api -n ${NAMESPACE} 2>/dev/null || true
    kubectl apply -f k8s/fixed/backend.yaml
    kubectl apply -f k8s/fixed/frontend.yaml
    kubectl apply -f k8s/fixed/network-policy.yaml
    echo -e "${GREEN}All fixes applied!${NC}"
    ;;
  *)
    echo -e "${RED}Invalid choice${NC}"
    exit 1
    ;;
esac

echo ""
echo -e "${YELLOW}Monitoring pod status...${NC}"
echo "Waiting for pods to stabilize..."
sleep 10

kubectl get pods -n ${NAMESPACE}

echo ""
echo -e "${GREEN}Check if the frontend is now healthy:${NC}"
echo "  kubectl get pods -n ${NAMESPACE} -l app=frontend"
echo "  kubectl logs -n ${NAMESPACE} -l app=frontend --tail=20"
echo ""
