#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Quick Start - Break-It-Friday${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if services are already running
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database API is already running on port 8000${NC}"
    API_RUNNING=true
else
    API_RUNNING=false
fi

if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is already running on port 3000${NC}"
    FRONTEND_RUNNING=true
else
    FRONTEND_RUNNING=false
fi

if [ "$API_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo ""
    echo -e "${GREEN}All services are running!${NC}"
    echo "  API: http://localhost:8000"
    echo "  Dashboard: http://localhost:3000"
    exit 0
fi

# Try Kubernetes first
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null 2>&1; then
    echo -e "${YELLOW}Kubernetes cluster detected. Starting services in K8s...${NC}"
    
    # Create namespace
    kubectl create namespace break-it-friday --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1
    
    # Deploy services
    echo -e "${YELLOW}Deploying services...${NC}"
    kubectl apply -f "${BASE_DIR}/k8s/services/database-api.yaml" > /dev/null 2>&1
    kubectl apply -f "${BASE_DIR}/k8s/services/frontend.yaml" > /dev/null 2>&1
    
    # Wait for deployments
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=120s deployment/database-api -n break-it-friday > /dev/null 2>&1 || true
    kubectl wait --for=condition=available --timeout=120s deployment/frontend -n break-it-friday > /dev/null 2>&1 || true
    
    # Check if port-forward processes exist
    if ! pgrep -f "kubectl port-forward.*database-api.*8000" > /dev/null; then
        echo -e "${YELLOW}Starting port-forward for Database API...${NC}"
        kubectl port-forward -n break-it-friday svc/database-api 8000:8000 > /dev/null 2>&1 &
        sleep 2
    fi
    
    if ! pgrep -f "kubectl port-forward.*frontend.*3000" > /dev/null; then
        echo -e "${YELLOW}Starting port-forward for Frontend...${NC}"
        kubectl port-forward -n break-it-friday svc/frontend 3000:80 > /dev/null 2>&1 &
        sleep 2
    fi
    
    # Verify services
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database API is accessible${NC}"
    else
        echo -e "${RED}✗ Database API not accessible. Check: kubectl get pods -n break-it-friday${NC}"
    fi
    
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is accessible${NC}"
    else
        echo -e "${RED}✗ Frontend not accessible. Check: kubectl get pods -n break-it-friday${NC}"
    fi
    
else
    # Start services locally
    echo -e "${YELLOW}No Kubernetes cluster found. Starting services locally...${NC}"
    
    # Start Database API
    if [ "$API_RUNNING" = false ]; then
        echo -e "${YELLOW}Starting Database API...${NC}"
        cd "${BASE_DIR}/apps/database-api"
        
        # Create virtual environment if needed
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -q -r requirements.txt > /dev/null 2>&1
        
        # Start in background
        nohup python3 app.py > /tmp/database-api.log 2>&1 &
        API_PID=$!
        echo $API_PID > /tmp/database-api.pid
        
        # Wait for API to start
        for i in {1..30}; do
            if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Database API started (PID: $API_PID)${NC}"
                break
            fi
            sleep 1
        done
        
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Database API failed to start. Check /tmp/database-api.log${NC}"
        fi
    fi
    
    # Start Frontend (simplified - just serve a simple HTML)
    if [ "$FRONTEND_RUNNING" = false ]; then
        echo -e "${YELLOW}Starting Frontend...${NC}"
        
        # Create a simple HTTP server for frontend
        cd "${BASE_DIR}/apps/frontend/public"
        
        # Start Python HTTP server
        nohup python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > /tmp/frontend.pid
        
        # Wait for frontend to start
        sleep 2
        if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
        else
            echo -e "${YELLOW}⚠ Frontend may need a moment to start${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Services Status${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Final verification
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database API: http://localhost:8000${NC}"
    echo "  Health: $(curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 || echo 'checking...')"
else
    echo -e "${RED}✗ Database API: Not accessible${NC}"
fi

if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend Dashboard: http://localhost:3000${NC}"
else
    echo -e "${RED}✗ Frontend: Not accessible${NC}"
fi

echo ""
echo -e "${BLUE}To stop services:${NC}"
if [ -f /tmp/database-api.pid ]; then
    echo "  kill \$(cat /tmp/database-api.pid)  # Stop Database API"
fi
if [ -f /tmp/frontend.pid ]; then
    echo "  kill \$(cat /tmp/frontend.pid)  # Stop Frontend"
fi
if pgrep -f "kubectl port-forward" > /dev/null; then
    echo "  pkill -f 'kubectl port-forward'  # Stop port-forwards"
fi

echo ""
echo -e "${GREEN}Access the dashboard at: http://localhost:3000${NC}"
