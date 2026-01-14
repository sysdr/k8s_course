#!/bin/bash

# Simple Docker deployment for PostgreSQL and Redis

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deploying Databases with Docker${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker stop postgres-break-it-friday redis-break-it-friday 2>/dev/null || true
docker rm postgres-break-it-friday redis-break-it-friday 2>/dev/null || true

# Start PostgreSQL
echo -e "${YELLOW}Starting PostgreSQL...${NC}"
docker run -d \
    --name postgres-break-it-friday \
    -e POSTGRES_DB=debugdb \
    -e POSTGRES_USER=debuguser \
    -e POSTGRES_PASSWORD=debugpass123 \
    -p 5432:5432 \
    --restart unless-stopped \
    postgres:15-alpine

echo -e "${GREEN}✓ PostgreSQL started${NC}"

# Start Redis
echo -e "${YELLOW}Starting Redis...${NC}"
docker run -d \
    --name redis-break-it-friday \
    -p 6379:6379 \
    --restart unless-stopped \
    redis:7-alpine

echo -e "${GREEN}✓ Redis started${NC}"

# Wait for services
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Test connections
if docker exec postgres-break-it-friday pg_isready -U debuguser > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL is starting...${NC}"
fi

if docker exec redis-break-it-friday redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${YELLOW}⚠ Redis is starting...${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Services Deployed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "PostgreSQL: localhost:5432"
echo "  Database: debugdb"
echo "  User: debuguser"
echo "  Password: debugpass123"
echo ""
echo "Redis: localhost:6379"
echo ""
echo -e "${YELLOW}Updating API to use localhost...${NC}"

# Update API environment to use localhost
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PID_FILE="/tmp/database-api.pid"

if [ -f "$API_PID_FILE" ]; then
    echo -e "${YELLOW}Restarting API with localhost configuration...${NC}"
    pkill -f "python3 app.py" 2>/dev/null || true
    sleep 2
    
    cd "${SCRIPT_DIR}/../apps/database-api"
    POSTGRES_HOST=localhost REDIS_HOST=localhost nohup python3 app.py > /tmp/database-api.log 2>&1 &
    echo $! > /tmp/database-api.pid
    
    sleep 3
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API restarted with localhost configuration${NC}"
    else
        echo -e "${YELLOW}⚠ API may need a moment to start${NC}"
    fi
fi

echo ""
echo -e "${GREEN}All services are ready!${NC}"
echo "  Dashboard: http://localhost:3000"
echo "  API: http://localhost:8000/health/all"
