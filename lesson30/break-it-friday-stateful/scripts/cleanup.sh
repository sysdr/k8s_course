#!/bin/bash

# Comprehensive cleanup script for Break-It-Friday project
# Stops all services, Docker containers, and removes unused resources

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Break-It-Friday Cleanup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Stop all services
echo -e "${YELLOW}Step 1: Stopping all services...${NC}"
if [ -f "${SCRIPT_DIR}/stop-services.sh" ]; then
    bash "${SCRIPT_DIR}/stop-services.sh" > /dev/null 2>&1
    echo -e "${GREEN}✓ Services stopped${NC}"
else
    # Manual stop
    pkill -f "python3 app.py" 2>/dev/null && echo -e "${GREEN}✓ API stopped${NC}" || true
    pkill -f "python3.*http.server.*3000" 2>/dev/null && echo -e "${GREEN}✓ Frontend stopped${NC}" || true
    pkill -f "kubectl port-forward" 2>/dev/null && echo -e "${GREEN}✓ Port forwards stopped${NC}" || true
fi

# Step 2: Stop and remove Docker containers
echo -e "${YELLOW}Step 2: Stopping and removing Docker containers...${NC}"
if command -v docker &> /dev/null; then
    # Stop containers
    docker stop postgres-break-it-friday redis-break-it-friday 2>/dev/null && \
        echo -e "${GREEN}✓ Docker containers stopped${NC}" || echo -e "${YELLOW}⚠ No containers to stop${NC}"
    
    # Remove containers
    docker rm postgres-break-it-friday redis-break-it-friday 2>/dev/null && \
        echo -e "${GREEN}✓ Docker containers removed${NC}" || echo -e "${YELLOW}⚠ No containers to remove${NC}"
else
    echo -e "${YELLOW}⚠ Docker not installed${NC}"
fi

# Step 3: Remove unused Docker resources
echo -e "${YELLOW}Step 3: Cleaning up unused Docker resources...${NC}"
if command -v docker &> /dev/null; then
    # Remove unused containers
    UNUSED_CONTAINERS=$(docker ps -a -f status=exited -q 2>/dev/null | wc -l)
    if [ "$UNUSED_CONTAINERS" -gt 0 ]; then
        docker container prune -f > /dev/null 2>&1
        echo -e "${GREEN}✓ Removed unused containers${NC}"
    else
        echo -e "${YELLOW}⚠ No unused containers${NC}"
    fi
    
    # Remove unused images (only dangling)
    DANGLING_IMAGES=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
    if [ "$DANGLING_IMAGES" -gt 0 ]; then
        docker image prune -f > /dev/null 2>&1
        echo -e "${GREEN}✓ Removed dangling images${NC}"
    else
        echo -e "${YELLOW}⚠ No dangling images${NC}"
    fi
    
    # Remove unused volumes
    UNUSED_VOLUMES=$(docker volume ls -f dangling=true -q 2>/dev/null | wc -l)
    if [ "$UNUSED_VOLUMES" -gt 0 ]; then
        docker volume prune -f > /dev/null 2>&1
        echo -e "${GREEN}✓ Removed unused volumes${NC}"
    else
        echo -e "${YELLOW}⚠ No unused volumes${NC}"
    fi
    
    # Remove unused networks
    docker network prune -f > /dev/null 2>&1 && \
        echo -e "${GREEN}✓ Cleaned unused networks${NC}" || true
else
    echo -e "${YELLOW}⚠ Docker not installed${NC}"
fi

# Step 4: Remove project-specific files
echo -e "${YELLOW}Step 4: Removing project files (node_modules, venv, cache)...${NC}"

# Remove node_modules
NODE_MODULES=$(find "${BASE_DIR}" -type d -name "node_modules" 2>/dev/null | wc -l)
if [ "$NODE_MODULES" -gt 0 ]; then
    find "${BASE_DIR}" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✓ Removed node_modules directories${NC}"
else
    echo -e "${YELLOW}⚠ No node_modules found${NC}"
fi

# Remove venv directories
VENV_DIRS=$(find "${BASE_DIR}" -type d -name "venv" 2>/dev/null | wc -l)
if [ "$VENV_DIRS" -gt 0 ]; then
    find "${BASE_DIR}" -type d -name "venv" -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✓ Removed venv directories${NC}"
else
    echo -e "${YELLOW}⚠ No venv directories found${NC}"
fi

# Remove __pycache__ directories
PYCACHE=$(find "${BASE_DIR}" -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$PYCACHE" -gt 0 ]; then
    find "${BASE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✓ Removed __pycache__ directories${NC}"
else
    echo -e "${YELLOW}⚠ No __pycache__ found${NC}"
fi

# Remove .pyc and .pyo files
PYC_FILES=$(find "${BASE_DIR}" -type f \( -name "*.pyc" -o -name "*.pyo" \) 2>/dev/null | wc -l)
if [ "$PYC_FILES" -gt 0 ]; then
    find "${BASE_DIR}" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null
    echo -e "${GREEN}✓ Removed .pyc/.pyo files${NC}"
else
    echo -e "${YELLOW}⚠ No .pyc/.pyo files found${NC}"
fi

# Remove .pytest_cache
PYTEST_CACHE=$(find "${BASE_DIR}" -type d -name ".pytest_cache" 2>/dev/null | wc -l)
if [ "$PYTEST_CACHE" -gt 0 ]; then
    find "${BASE_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✓ Removed .pytest_cache directories${NC}"
else
    echo -e "${YELLOW}⚠ No .pytest_cache found${NC}"
fi

# Remove Istio files
ISTIO_FILES=$(find "${BASE_DIR}" -type f \( -iname "*istio*" -o -iname "*Istio*" \) 2>/dev/null | wc -l)
if [ "$ISTIO_FILES" -gt 0 ]; then
    find "${BASE_DIR}" -type f \( -iname "*istio*" -o -iname "*Istio*" \) -delete 2>/dev/null
    echo -e "${GREEN}✓ Removed Istio files${NC}"
else
    echo -e "${YELLOW}⚠ No Istio files found${NC}"
fi

# Remove PID files
if [ -f /tmp/database-api.pid ]; then
    rm -f /tmp/database-api.pid
    echo -e "${GREEN}✓ Removed PID files${NC}"
fi

if [ -f /tmp/frontend.pid ]; then
    rm -f /tmp/frontend.pid
    echo -e "${GREEN}✓ Removed frontend PID file${NC}"
fi

# Remove log files
if [ -f /tmp/database-api.log ]; then
    rm -f /tmp/database-api.log
    echo -e "${GREEN}✓ Removed log files${NC}"
fi

if [ -f /tmp/frontend.log ]; then
    rm -f /tmp/frontend.log
    echo -e "${GREEN}✓ Removed frontend log file${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ All services stopped"
echo "  ✓ Docker containers stopped and removed"
echo "  ✓ Unused Docker resources cleaned"
echo "  ✓ Project files cleaned (node_modules, venv, cache, etc.)"
echo "  ✓ Temporary files removed"
echo ""
