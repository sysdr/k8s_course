#!/bin/bash

# Cleanup script - removes all resources

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Cleaning up debug challenge resources...${NC}"

kubectl delete namespace debug-challenge --ignore-not-found=true

echo -e "${YELLOW}Waiting for namespace deletion...${NC}"
kubectl wait --for=delete namespace/debug-challenge --timeout=60s 2>/dev/null || true

echo -e "${RED}Cleanup complete!${NC}"
