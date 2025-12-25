#!/bin/bash

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Cleaning up Kubernetes resources ===${NC}"

echo -e "\n${YELLOW}Deleting deployment job...${NC}"
kubectl delete job deployment-job -n ci-cd --ignore-not-found=true

echo -e "\n${YELLOW}Deleting application resources...${NC}"
kubectl delete -f k8s/applications/ --ignore-not-found=true

echo -e "\n${YELLOW}Deleting RBAC resources...${NC}"
kubectl delete -f k8s/rbac/broken/ --ignore-not-found=true
kubectl delete -f k8s/rbac/fixed/ --ignore-not-found=true

echo -e "\n${YELLOW}Deleting namespaces...${NC}"
kubectl delete namespace ci-cd staging production --ignore-not-found=true

echo -e "\n${GREEN}Cleanup complete${NC}"
