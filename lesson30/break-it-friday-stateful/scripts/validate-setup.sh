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
echo -e "${GREEN}Validating Break-It-Friday Setup${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} Missing: $description"
        ((ERRORS++))
        return 1
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} Missing: $description"
        ((ERRORS++))
        return 1
    fi
}

echo -e "${YELLOW}Checking directory structure...${NC}"
check_directory "${BASE_DIR}/scenarios" "Scenarios directory"
check_directory "${BASE_DIR}/solutions" "Solutions directory"
check_directory "${BASE_DIR}/apps" "Apps directory"
check_directory "${BASE_DIR}/k8s" "K8s directory"
check_directory "${BASE_DIR}/scripts" "Scripts directory"
check_directory "${BASE_DIR}/docs" "Docs directory"

echo ""
echo -e "${YELLOW}Checking scenario files...${NC}"
for i in {1..6}; do
    SCENARIO_DIR="${BASE_DIR}/scenarios/0${i}-"
    if [ $i -eq 1 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/01-pvc-pending"
        check_file "${SCENARIO_DIR}/postgres-statefulset.yaml" "Scenario 1 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 1 README"
    elif [ $i -eq 2 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/02-resource-quota"
        check_file "${SCENARIO_DIR}/quota-exhaustion.yaml" "Scenario 2 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 2 README"
    elif [ $i -eq 3 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/03-postgres-crashloop"
        check_file "${SCENARIO_DIR}/postgres-broken.yaml" "Scenario 3 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 3 README"
    elif [ $i -eq 4 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/04-volume-permissions"
        check_file "${SCENARIO_DIR}/permissions-broken.yaml" "Scenario 4 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 4 README"
    elif [ $i -eq 5 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/05-redis-antiaffinity"
        check_file "${SCENARIO_DIR}/redis-broken.yaml" "Scenario 5 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 5 README"
    elif [ $i -eq 6 ]; then
        SCENARIO_DIR="${BASE_DIR}/scenarios/06-storage-timeout"
        check_file "${SCENARIO_DIR}/cassandra-timeout.yaml" "Scenario 6 YAML"
        check_file "${SCENARIO_DIR}/README.md" "Scenario 6 README"
    fi
done

echo ""
echo -e "${YELLOW}Checking solution files...${NC}"
check_file "${BASE_DIR}/solutions/01-pvc-pending-FIXED.yaml" "Solution 1"
check_file "${BASE_DIR}/solutions/02-resource-quota-FIXED.yaml" "Solution 2"
check_file "${BASE_DIR}/solutions/03-postgres-crashloop-FIXED.yaml" "Solution 3"
check_file "${BASE_DIR}/solutions/04-volume-permissions-FIXED.yaml" "Solution 4"
check_file "${BASE_DIR}/solutions/05-redis-antiaffinity-FIXED.yaml" "Solution 5"
check_file "${BASE_DIR}/solutions/06-storage-timeout-FIXED.yaml" "Solution 6"

echo ""
echo -e "${YELLOW}Checking application files...${NC}"
check_file "${BASE_DIR}/apps/database-api/app.py" "Database API app"
check_file "${BASE_DIR}/apps/database-api/requirements.txt" "Database API requirements"
check_file "${BASE_DIR}/apps/database-api/Dockerfile" "Database API Dockerfile"
check_file "${BASE_DIR}/apps/storage-monitor/monitor.py" "Storage Monitor app"
check_file "${BASE_DIR}/apps/storage-monitor/requirements.txt" "Storage Monitor requirements"
check_file "${BASE_DIR}/apps/storage-monitor/Dockerfile" "Storage Monitor Dockerfile"
check_file "${BASE_DIR}/apps/frontend/src/App.js" "Frontend App.js"
check_file "${BASE_DIR}/apps/frontend/src/index.js" "Frontend index.js"
check_file "${BASE_DIR}/apps/frontend/package.json" "Frontend package.json"
check_file "${BASE_DIR}/apps/frontend/Dockerfile" "Frontend Dockerfile"

echo ""
echo -e "${YELLOW}Checking Kubernetes manifests...${NC}"
check_file "${BASE_DIR}/k8s/storage/storageclass.yaml" "StorageClass manifest"
check_file "${BASE_DIR}/k8s/monitoring/prometheus-config.yaml" "Prometheus config"
check_file "${BASE_DIR}/k8s/services/database-api.yaml" "Database API deployment"
check_file "${BASE_DIR}/k8s/services/frontend.yaml" "Frontend deployment"
check_file "${BASE_DIR}/k8s/services/storage-monitor.yaml" "Storage Monitor deployment"

echo ""
echo -e "${YELLOW}Checking scripts...${NC}"
check_file "${BASE_DIR}/scripts/setup-cluster.sh" "Setup cluster script"
check_file "${BASE_DIR}/scripts/deploy-scenarios.sh" "Deploy scenarios script"
check_file "${BASE_DIR}/scripts/check-status.sh" "Check status script"
check_file "${BASE_DIR}/scripts/cleanup.sh" "Cleanup script"
check_file "${BASE_DIR}/scripts/start-services.sh" "Start services script"
check_file "${BASE_DIR}/scripts/run-tests.sh" "Run tests script"
check_file "${BASE_DIR}/scripts/run-demo.sh" "Run demo script"
check_file "${BASE_DIR}/scripts/check-duplicates.sh" "Check duplicates script"

echo ""
echo -e "${YELLOW}Checking documentation...${NC}"
check_file "${BASE_DIR}/README.md" "Main README"
check_file "${BASE_DIR}/docs/debugging-methodology.md" "Debugging methodology"

echo ""
echo -e "${GREEN}================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All files validated successfully!${NC}"
    exit 0
else
    echo -e "${RED}✗ Found ${ERRORS} missing file(s)${NC}"
    exit 1
fi
