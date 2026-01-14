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
echo -e "${GREEN}Deploying PostgreSQL and Redis${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl is not installed${NC}"
    echo -e "${YELLOW}Deploying using Docker instead...${NC}"
    
    # Deploy using Docker
    deploy_with_docker
    exit 0
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null 2>&1; then
    echo -e "${YELLOW}No Kubernetes cluster found. Deploying using Docker...${NC}"
    deploy_with_docker
    exit 0
fi

echo -e "${YELLOW}Deploying to Kubernetes...${NC}"

# Deploy PostgreSQL
echo -e "${YELLOW}Deploying PostgreSQL...${NC}"
kubectl apply -f "${BASE_DIR}/k8s/services/postgres-standalone.yaml"

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/postgres -n scenario-01 || true

# Deploy Redis
echo -e "${YELLOW}Deploying Redis...${NC}"
kubectl apply -f "${BASE_DIR}/k8s/services/redis-standalone.yaml"

# Wait for Redis
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/redis -n scenario-05 || true

# Get service endpoints
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Services Deployed${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

PG_IP=$(kubectl get svc postgres -n scenario-01 -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "pending")
REDIS_IP=$(kubectl get svc redis -n scenario-05 -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "pending")

echo -e "${BLUE}PostgreSQL:${NC}"
echo "  Service: postgres.scenario-01.svc.cluster.local"
echo "  IP: ${PG_IP}"
kubectl get pods -n scenario-01 -l app=postgres 2>/dev/null | tail -1

echo ""
echo -e "${BLUE}Redis:${NC}"
echo "  Service: redis.scenario-05.svc.cluster.local"
echo "  IP: ${REDIS_IP}"
kubectl get pods -n scenario-05 -l app=redis 2>/dev/null | tail -1

echo ""
echo -e "${GREEN}Services are being deployed. Wait a minute for them to be ready.${NC}"
echo -e "${YELLOW}Check status with: kubectl get pods -n scenario-01,scenario-05${NC}"

deploy_with_docker() {
    echo -e "${YELLOW}Deploying PostgreSQL with Docker...${NC}"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker is not installed${NC}"
        echo -e "${YELLOW}Please install Docker or set up a Kubernetes cluster${NC}"
        exit 1
    fi
    
    # Start PostgreSQL
    docker run -d \
        --name postgres-break-it-friday \
        -e POSTGRES_DB=debugdb \
        -e POSTGRES_USER=debuguser \
        -e POSTGRES_PASSWORD=debugpass123 \
        -p 5432:5432 \
        --restart unless-stopped \
        postgres:15-alpine > /dev/null 2>&1
    
    echo -e "${GREEN}✓ PostgreSQL started on localhost:5432${NC}"
    
    # Start Redis
    echo -e "${YELLOW}Deploying Redis with Docker...${NC}"
    docker run -d \
        --name redis-break-it-friday \
        -p 6379:6379 \
        --restart unless-stopped \
        redis:7-alpine > /dev/null 2>&1
    
    echo -e "${GREEN}✓ Redis started on localhost:6379${NC}"
    
    echo ""
    echo -e "${GREEN}Services are running!${NC}"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    
    # Update API to use localhost
    echo ""
    echo -e "${YELLOW}Updating API configuration...${NC}"
    # The API already defaults to 'postgres' and 'redis' hostnames
    # For Docker, we need to update the API to use localhost
    echo -e "${YELLOW}Note: API is configured for Kubernetes service names.${NC}"
    echo -e "${YELLOW}For Docker, update API environment variables to use 'localhost'${NC}"
}
