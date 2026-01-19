#!/bin/bash

set -euo pipefail

# Blue-Green deployment switcher
# Manages traffic switching between blue and green environments

NAMESPACE="progressive-delivery"
SERVICE="order-service"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

get_current_version() {
    kubectl get service $SERVICE -n $NAMESPACE -o jsonpath='{.spec.selector.color}'
}

switch_traffic() {
    local target=$1
    
    echo -e "${BLUE}Switching traffic to: $target${NC}"
    
    kubectl patch service $SERVICE -n $NAMESPACE --type merge -p "{\"spec\":{\"selector\":{\"color\":\"$target\"}}}"
    
    echo -e "${GREEN}✓ Traffic switched to $target${NC}"
    
    # Verify
    sleep 2
    local current=$(get_current_version)
    echo "Current active version: $current"
}

validate_deployment() {
    local color=$1
    
    echo "Validating $color deployment..."
    
    local ready_pods=$(kubectl get pods -n $NAMESPACE -l app=$SERVICE,color=$color -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' | wc -w)
    
    if [ "$ready_pods" -eq 0 ]; then
        echo -e "${RED}✗ No running pods for $color${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ $color deployment has $ready_pods running pods${NC}"
    return 0
}

# Main logic
CURRENT=$(get_current_version)
echo "Current active: $CURRENT"

if [ "$CURRENT" == "blue" ]; then
    TARGET="green"
else
    TARGET="blue"
fi

echo ""
echo "Blue-Green Deployment Switch"
echo "============================="
echo "Current: $CURRENT"
echo "Target:  $TARGET"
echo ""

if validate_deployment "$TARGET"; then
    read -p "Switch traffic to $TARGET? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        switch_traffic "$TARGET"
    else
        echo "Switch cancelled"
    fi
else
    echo -e "${RED}Cannot switch to $TARGET - deployment not ready${NC}"
    exit 1
fi
