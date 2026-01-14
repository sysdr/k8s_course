#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "Verifying database connections..."

# Check Docker containers
echo -e "\n${YELLOW}Docker Containers:${NC}"
if docker ps | grep -q postgres-break-it-friday; then
    echo -e "${GREEN}✓ PostgreSQL container running${NC}"
else
    echo -e "${RED}✗ PostgreSQL container not running${NC}"
fi

if docker ps | grep -q redis-break-it-friday; then
    echo -e "${GREEN}✓ Redis container running${NC}"
else
    echo -e "${RED}✗ Redis container not running${NC}"
fi

# Test connections
echo -e "\n${YELLOW}Database Connections:${NC}"
if docker exec postgres-break-it-friday pg_isready -U debuguser > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL not ready${NC}"
fi

if docker exec redis-break-it-friday redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}✗ Redis not ready${NC}"
fi

# Check API
echo -e "\n${YELLOW}API Status:${NC}"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running${NC}"
    
    # Check health endpoints
    PG_STATUS=$(curl -s http://localhost:8000/health/postgres 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    REDIS_STATUS=$(curl -s http://localhost:8000/health/redis 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    
    echo "  PostgreSQL: ${PG_STATUS}"
    echo "  Redis: ${REDIS_STATUS}"
else
    echo -e "${RED}✗ API is not running${NC}"
    echo -e "${YELLOW}Start with: ./start-simple.sh${NC}"
fi

echo ""
