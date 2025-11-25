#!/bin/bash

# Debug Guide Script - Systematic debugging methodology
# This script walks you through debugging the broken application

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="debug-challenge"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Kubernetes Debugging Guide${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: State Assessment
echo -e "${YELLOW}STEP 1: State Assessment${NC}"
echo "Let's see the current state of all pods..."
echo ""
kubectl get pods -n ${NAMESPACE} -o wide --show-labels
echo ""
echo -e "${GREEN}Analysis Questions:${NC}"
echo "1. Which pods are in CrashLoopBackOff?"
echo "2. What are the restart counts?"
echo "3. Which nodes are the pods running on?"
echo ""
read -p "Press Enter to continue to Step 2..."
echo ""

# Step 2: Event Investigation
echo -e "${YELLOW}STEP 2: Event Investigation${NC}"
echo "Checking Kubernetes events for failure indicators..."
echo ""
kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'
echo ""
echo -e "${GREEN}Look for:${NC}"
echo "- BackOff events (container crashes)"
echo "- FailedScheduling (resource constraints)"
echo "- Unhealthy (probe failures)"
echo ""
read -p "Press Enter to continue to Step 3..."
echo ""

# Step 3: Detailed Pod Description
echo -e "${YELLOW}STEP 3: Detailed Pod Investigation${NC}"
echo "Getting detailed information about the frontend pod..."
echo ""
FRONTEND_POD=$(kubectl get pods -n ${NAMESPACE} -l app=frontend -o jsonpath='{.items[0].metadata.name}')
echo -e "${BLUE}Frontend Pod: ${FRONTEND_POD}${NC}"
echo ""
kubectl describe pod ${FRONTEND_POD} -n ${NAMESPACE}
echo ""
read -p "Press Enter to continue to Step 4..."
echo ""

# Step 4: Log Analysis
echo -e "${YELLOW}STEP 4: Log Analysis${NC}"
echo "Examining frontend logs for error messages..."
echo ""
echo -e "${BLUE}Current logs:${NC}"
kubectl logs ${FRONTEND_POD} -n ${NAMESPACE} --tail=50
echo ""
echo -e "${BLUE}Previous crash logs (if available):${NC}"
kubectl logs ${FRONTEND_POD} -n ${NAMESPACE} --previous --tail=50 2>/dev/null || echo "No previous logs available"
echo ""
echo -e "${GREEN}Key Questions:${NC}"
echo "1. What error message appears in the logs?"
echo "2. What URL is the frontend trying to connect to?"
echo "3. Is it a connection refused or DNS resolution error?"
echo ""
read -p "Press Enter to continue to Step 5..."
echo ""

# Step 5: Service Investigation
echo -e "${YELLOW}STEP 5: Service Investigation${NC}"
echo "Checking all services in the namespace..."
echo ""
kubectl get svc -n ${NAMESPACE}
echo ""
echo -e "${GREEN}Analysis:${NC}"
echo "1. Does the service the frontend is trying to reach exist?"
echo "2. Does the service name match what's in the logs?"
echo "3. Check the service selector:"
echo ""
kubectl get svc -n ${NAMESPACE} -o yaml | grep -A 5 selector
echo ""
read -p "Press Enter to continue to Step 6..."
echo ""

# Step 6: Connectivity Testing
echo -e "${YELLOW}STEP 6: Connectivity Testing${NC}"
echo "Testing DNS resolution from frontend pod..."
echo ""
echo -e "${BLUE}Testing DNS for 'api-backend':${NC}"
kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- nslookup api-backend 2>/dev/null || echo "DNS resolution failed"
echo ""
echo -e "${BLUE}Testing DNS for 'backend-api':${NC}"
kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- nslookup backend-api 2>/dev/null || echo "DNS resolution failed"
echo ""
echo -e "${GREEN}Which one resolved successfully?${NC}"
echo ""
read -p "Press Enter to continue to Step 7..."
echo ""

# Step 7: Solution Identification
echo -e "${YELLOW}STEP 7: Identifying the Solution${NC}"
echo ""
echo -e "${RED}COMMON ISSUES FOUND:${NC}"
echo ""
echo -e "${YELLOW}Issue #1: Service Name Mismatch${NC}"
echo "Frontend environment variable: API_URL=http://api-backend:8000"
echo "Actual service name: backend-api"
echo ""
echo -e "${GREEN}Possible Fixes:${NC}"
echo "A) Rename the service to match the frontend expectation"
echo "B) Update the frontend environment variable"
echo ""
echo -e "${YELLOW}Issue #2: Missing Service${NC}"
echo "If no service exists, create one with correct selector"
echo ""
echo -e "${YELLOW}Issue #3: Network Policy${NC}"
echo "Check if NetworkPolicies are blocking traffic"
kubectl get networkpolicies -n ${NAMESPACE}
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Ready to apply fixes?${NC}"
echo "Run './scripts/apply-fixes.sh' to apply the corrections"
echo -e "${BLUE}========================================${NC}"
