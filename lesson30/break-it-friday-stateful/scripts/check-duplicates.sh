#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Checking for Duplicate Services${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

DUPLICATES_FOUND=0

# Check for duplicate processes
echo -e "${YELLOW}Checking for duplicate processes...${NC}"

# Check Python processes (database-api, storage-monitor)
PYTHON_PROCS=$(ps aux | grep -E "python.*app\.py|python.*monitor\.py" | grep -v grep | wc -l)
if [ "$PYTHON_PROCS" -gt 2 ]; then
    echo -e "${RED}⚠ Found ${PYTHON_PROCS} Python service processes (expected max 2)${NC}"
    ps aux | grep -E "python.*app\.py|python.*monitor\.py" | grep -v grep
    ((DUPLICATES_FOUND++))
else
    echo -e "${GREEN}✓ Python services: ${PYTHON_PROCS} processes${NC}"
fi

# Check Node processes (frontend)
NODE_PROCS=$(ps aux | grep -E "node.*react-scripts|npm.*start" | grep -v grep | wc -l)
if [ "$NODE_PROCS" -gt 1 ]; then
    echo -e "${RED}⚠ Found ${NODE_PROCS} Node.js processes (expected max 1)${NC}"
    ps aux | grep -E "node.*react-scripts|npm.*start" | grep -v grep
    ((DUPLICATES_FOUND++))
else
    echo -e "${GREEN}✓ Node.js services: ${NODE_PROCS} processes${NC}"
fi

# Check Kubernetes deployments if kubectl is available
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null 2>&1; then
    echo ""
    echo -e "${YELLOW}Checking Kubernetes deployments...${NC}"
    
    # Check for duplicate replicas beyond expected
    for deployment in database-api frontend storage-monitor; do
        REPLICAS=$(kubectl get deployment "$deployment" -n break-it-friday -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        READY=$(kubectl get deployment "$deployment" -n break-it-friday -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        
        if [ "$REPLICAS" != "0" ] && [ "$REPLICAS" != "1" ]; then
            echo -e "${YELLOW}⚠ Deployment ${deployment}: ${REPLICAS} replicas (${READY} ready)${NC}"
        elif [ "$REPLICAS" = "1" ]; then
            echo -e "${GREEN}✓ Deployment ${deployment}: ${READY}/${REPLICAS} ready${NC}"
        fi
    done
    
    # Check for duplicate services
    echo ""
    echo -e "${YELLOW}Checking Kubernetes services...${NC}"
    SERVICE_COUNT=$(kubectl get svc -n break-it-friday --no-headers 2>/dev/null | wc -l)
    if [ "$SERVICE_COUNT" -gt 3 ]; then
        echo -e "${RED}⚠ Found ${SERVICE_COUNT} services in break-it-friday namespace (expected max 3)${NC}"
        kubectl get svc -n break-it-friday
        ((DUPLICATES_FOUND++))
    else
        echo -e "${GREEN}✓ Services: ${SERVICE_COUNT} found${NC}"
    fi
fi

# Check ports
echo ""
echo -e "${YELLOW}Checking for port conflicts...${NC}"

check_port() {
    local port=$1
    local service=$2
    
    if command -v lsof &> /dev/null; then
        PORT_USERS=$(lsof -i :$port 2>/dev/null | wc -l)
        if [ "$PORT_USERS" -gt 1 ]; then
            echo -e "${RED}⚠ Port ${port} (${service}) has multiple listeners${NC}"
            lsof -i :$port 2>/dev/null | grep -v COMMAND
            ((DUPLICATES_FOUND++))
        elif [ "$PORT_USERS" -eq 1 ]; then
            echo -e "${GREEN}✓ Port ${port} (${service}): 1 listener${NC}"
        fi
    elif command -v netstat &> /dev/null; then
        PORT_USERS=$(netstat -tuln 2>/dev/null | grep ":$port " | wc -l)
        if [ "$PORT_USERS" -gt 1 ]; then
            echo -e "${RED}⚠ Port ${port} (${service}) has multiple listeners${NC}"
            ((DUPLICATES_FOUND++))
        elif [ "$PORT_USERS" -eq 1 ]; then
            echo -e "${GREEN}✓ Port ${port} (${service}): 1 listener${NC}"
        fi
    fi
}

check_port 8000 "Database API"
check_port 3000 "Frontend"

# Summary
echo ""
echo -e "${GREEN}================================${NC}"
if [ $DUPLICATES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No duplicate services found${NC}"
    exit 0
else
    echo -e "${RED}⚠ Found ${DUPLICATES_FOUND} potential duplicate service(s)${NC}"
    exit 1
fi
