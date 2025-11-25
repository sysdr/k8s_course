#!/bin/bash

# Deploy the broken version for debugging practice

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Deploying broken e-commerce application...${NC}"
echo ""

# Create namespace
echo -e "${GREEN}Creating namespace...${NC}"
kubectl apply -f k8s/broken/namespace.yaml

# Deploy database
echo -e "${GREEN}Deploying PostgreSQL database...${NC}"
kubectl apply -f k8s/broken/postgres.yaml

# Wait for database
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n debug-challenge --timeout=120s

# Deploy backend (with bug)
echo -e "${GREEN}Deploying backend API (contains bugs)...${NC}"
kubectl apply -f k8s/broken/backend.yaml

# Wait for backend
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
sleep 10

# Deploy frontend (with bug)
echo -e "${GREEN}Deploying frontend (will fail due to bugs)...${NC}"
kubectl apply -f k8s/broken/frontend.yaml

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Deployment complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}The application is now deployed in a broken state.${NC}"
echo "Frontend pods should be in CrashLoopBackOff."
echo ""
echo "Check status with:"
echo "  kubectl get pods -n debug-challenge"
echo ""
echo "Start debugging with:"
echo "  ./scripts/debug-guide.sh"
echo ""
