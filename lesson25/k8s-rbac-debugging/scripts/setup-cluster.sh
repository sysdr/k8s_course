#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Kubernetes Cluster Setup ===${NC}"

# Check if kind is installed
if command -v kind &> /dev/null; then
    echo -e "${GREEN}✓ kind is installed${NC}"
    
    if kind get clusters | grep -q "rbac-debugging"; then
        echo -e "${YELLOW}Cluster 'rbac-debugging' already exists${NC}"
        read -p "Delete and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kind delete cluster --name rbac-debugging
        else
            echo "Using existing cluster"
            kubectl cluster-info --context kind-rbac-debugging
            exit 0
        fi
    fi
    
    echo -e "${YELLOW}Creating kind cluster 'rbac-debugging'...${NC}"
    kind create cluster --name rbac-debugging --config - <<EOF_KIND
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF_KIND
    
    echo -e "${GREEN}✓ Cluster created successfully${NC}"
    kubectl cluster-info --context kind-rbac-debugging
    
# Check if minikube is installed
elif command -v minikube &> /dev/null; then
    echo -e "${GREEN}✓ minikube is installed${NC}"
    
    if minikube status | grep -q "Running"; then
        echo -e "${YELLOW}Minikube is already running${NC}"
        kubectl cluster-info
        exit 0
    fi
    
    echo -e "${YELLOW}Starting minikube...${NC}"
    minikube start --driver=docker --cpus=2 --memory=4096
    
    echo -e "${GREEN}✓ Minikube started successfully${NC}"
    kubectl cluster-info
    
else
    echo -e "${RED}✗ Neither kind nor minikube found${NC}"
    echo "Please install one of:"
    echo "  - kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    echo "  - minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

echo -e "\n${GREEN}=== Cluster ready for deployment ===${NC}"
echo "Run: cd $(basename "${PWD}") && ./scripts/deploy.sh broken"
