#!/bin/bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Starting Break-It-Friday Services${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

MODE="${1:-k8s}"

if [ "$MODE" = "local" ]; then
    echo -e "${YELLOW}Starting services locally...${NC}"
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: python3 is not installed${NC}"
        exit 1
    fi
    
    # Start Database API
    echo -e "${YELLOW}Starting Database API...${NC}"
    cd "${BASE_DIR}/apps/database-api"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r requirements.txt
    python3 app.py &
    DB_API_PID=$!
    echo -e "${GREEN}✓ Database API started (PID: $DB_API_PID)${NC}"
    echo "  API available at: http://localhost:8000"
    
    # Start Frontend (if Node.js is available)
    if command -v npm &> /dev/null; then
        echo -e "${YELLOW}Starting Frontend...${NC}"
        cd "${BASE_DIR}/apps/frontend"
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        REACT_APP_API_URL=http://localhost:8000 npm start &
        FRONTEND_PID=$!
        echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
        echo "  Frontend available at: http://localhost:3000"
    else
        echo -e "${YELLOW}Node.js not found, skipping frontend${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Services started locally!${NC}"
    echo "To stop services, run: pkill -f 'python3 app.py' && pkill -f 'react-scripts'"
    
elif [ "$MODE" = "k8s" ]; then
    echo -e "${YELLOW}Deploying services to Kubernetes...${NC}"
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}ERROR: kubectl is not installed${NC}"
        exit 1
    fi
    
    # Check if we can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}ERROR: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    # Create namespace for services
    kubectl create namespace break-it-friday --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Database API
    echo -e "${YELLOW}Deploying Database API...${NC}"
    kubectl apply -f "${BASE_DIR}/k8s/services/database-api.yaml"
    kubectl rollout status deployment/database-api -n break-it-friday --timeout=120s || true
    
    # Deploy Frontend
    echo -e "${YELLOW}Deploying Frontend...${NC}"
    kubectl apply -f "${BASE_DIR}/k8s/services/frontend.yaml"
    kubectl rollout status deployment/frontend -n break-it-friday --timeout=120s || true
    
    # Deploy Storage Monitor
    echo -e "${YELLOW}Deploying Storage Monitor...${NC}"
    kubectl apply -f "${BASE_DIR}/k8s/services/storage-monitor.yaml"
    kubectl rollout status deployment/storage-monitor -n break-it-friday --timeout=120s || true
    
    echo ""
    echo -e "${GREEN}Services deployed!${NC}"
    echo ""
    echo "Get service URLs:"
    echo "  kubectl get svc -n break-it-friday"
    echo ""
    echo "Port forward to access locally:"
    echo "  kubectl port-forward -n break-it-friday svc/database-api 8000:8000"
    echo "  kubectl port-forward -n break-it-friday svc/frontend 3000:80"
    
else
    echo -e "${RED}ERROR: Invalid mode. Use 'local' or 'k8s'${NC}"
    exit 1
fi
