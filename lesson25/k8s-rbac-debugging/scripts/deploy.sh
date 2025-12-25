#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODE="${1:-broken}"

echo -e "${GREEN}=== Kubernetes RBAC Debugging Deployment ===${NC}"
echo -e "${YELLOW}Mode: ${MODE}${NC}\n"

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

echo -e "${YELLOW}[1/6] Creating namespaces...${NC}"
kubectl apply -f k8s/namespaces/namespaces.yaml

echo -e "\n${YELLOW}[2/6] Building Docker images...${NC}"
echo "Building deployer image..."
docker build -t deployer:latest app/deployer/ -q

echo "Building sample-app image..."
docker build -t sample-app:latest app/sample-app/ -q

# Load images into cluster if using kind
if kubectl config current-context | grep -q "kind"; then
    echo "Loading images into kind cluster..."
    CLUSTER_NAME=$(kubectl config current-context | sed 's/kind-//')
    kind load docker-image deployer:latest --name "${CLUSTER_NAME}" || echo "Warning: Failed to load deployer image (may already be loaded)"
    kind load docker-image sample-app:latest --name "${CLUSTER_NAME}" || echo "Warning: Failed to load sample-app image (may already be loaded)"
fi

echo -e "\n${YELLOW}[3/6] Deploying RBAC configuration (${MODE})...${NC}"
if [ "${MODE}" = "broken" ]; then
    echo -e "${RED}Deploying BROKEN RBAC configuration${NC}"
    kubectl apply -f k8s/rbac/broken/
elif [ "${MODE}" = "fixed" ]; then
    echo -e "${GREEN}Deploying FIXED RBAC configuration${NC}"
    kubectl apply -f k8s/rbac/fixed/
else
    echo -e "${RED}Invalid mode: ${MODE}${NC}"
    echo "Usage: $0 [broken|fixed]"
    exit 1
fi

echo -e "\n${YELLOW}[4/6] Waiting for ServiceAccount to be ready...${NC}"
sleep 2

echo -e "\n${YELLOW}[5/6] Launching deployment job...${NC}"
# Delete previous job if exists
kubectl delete job deployment-job -n ci-cd --ignore-not-found=true

# Create new job
kubectl apply -f k8s/ci-cd/deployer-job.yaml

echo -e "\n${YELLOW}[6/6] Monitoring deployment job...${NC}"
echo -e "${YELLOW}Waiting for job to start...${NC}"
sleep 3

# Get pod name
POD_NAME=$(kubectl get pods -n ci-cd -l app=ci-cd-deployer --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null || echo "")

if [ -z "${POD_NAME}" ]; then
    echo -e "${RED}Failed to find deployer pod${NC}"
    exit 1
fi

echo -e "${GREEN}Following logs from pod: ${POD_NAME}${NC}\n"
echo "======================================================================"
kubectl logs -f "${POD_NAME}" -n ci-cd || true
echo "======================================================================"

# Check job status
echo -e "\n${YELLOW}Checking job completion status...${NC}"
JOB_STATUS=$(kubectl get job deployment-job -n ci-cd -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "Unknown")

if [ "${JOB_STATUS}" = "Complete" ]; then
    echo -e "${GREEN}✓ Deployment job completed successfully${NC}"
    
    echo -e "\n${YELLOW}Checking deployed resources in production namespace:${NC}"
    kubectl get deployments,services,pods -n production
    
    if [ "${MODE}" = "broken" ]; then
        echo -e "\n${YELLOW}Wait, the job succeeded with broken RBAC?${NC}"
        echo -e "${YELLOW}This shouldn't happen - check the logs above${NC}"
    fi
elif [ "${JOB_STATUS}" = "Failed" ]; then
    echo -e "${RED}✗ Deployment job failed${NC}"
    
    if [ "${MODE}" = "broken" ]; then
        echo -e "\n${GREEN}This is expected with broken RBAC!${NC}"
        echo -e "${YELLOW}Run the debugging script to diagnose:${NC}"
        echo "  ./scripts/debugging/diagnose-rbac.sh"
    else
        echo -e "\n${RED}Job failed with fixed RBAC - unexpected!${NC}"
        echo -e "${YELLOW}Check the logs above for details${NC}"
    fi
else
    echo -e "${YELLOW}Job status: ${JOB_STATUS}${NC}"
fi

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
