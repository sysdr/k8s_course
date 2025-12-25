#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DASHBOARD_DIR="${PROJECT_ROOT}/dashboard"

echo -e "${GREEN}=== Starting RBAC Debugging Dashboard ===${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure your cluster is running (kind, minikube, or other)"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "${DASHBOARD_DIR}/venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    cd "${DASHBOARD_DIR}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
cd "${DASHBOARD_DIR}"
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the dashboard
echo -e "${GREEN}Starting dashboard server...${NC}"
echo -e "${YELLOW}Dashboard will be available at: http://localhost:8080${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

python app.py

