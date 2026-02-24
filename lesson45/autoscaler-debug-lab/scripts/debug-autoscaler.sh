#!/bin/bash

# Comprehensive Cluster Autoscaler Debugging Script

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Cluster Autoscaler Debug Utility${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Check 1: Verify autoscaler is running
echo -e "${YELLOW}[1/8] Checking autoscaler deployment status...${NC}"
if kubectl get deployment cluster-autoscaler -n kube-system &>/dev/null; then
    REPLICAS=$(kubectl get deployment cluster-autoscaler -n kube-system -o jsonpath='{.status.readyReplicas}')
    if [[ "$REPLICAS" == "1" ]]; then
        echo -e "${GREEN}✓ Autoscaler is running${NC}"
    else
        echo -e "${RED}✗ Autoscaler is not ready (ready replicas: $REPLICAS)${NC}"
    fi
else
    echo -e "${RED}✗ Autoscaler deployment not found${NC}"
fi

# Check 2: Review pending pods
echo -e "\n${YELLOW}[2/8] Checking for pending pods...${NC}"
PENDING_PODS=$(kubectl get pods --all-namespaces --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l)
if [[ $PENDING_PODS -gt 0 ]]; then
    echo -e "${RED}✗ Found $PENDING_PODS pending pod(s)${NC}"
    echo -e "${BLUE}Details:${NC}"
    kubectl get pods --all-namespaces --field-selector=status.phase=Pending -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,REASON:.status.conditions[0].reason
else
    echo -e "${GREEN}✓ No pending pods${NC}"
fi

# Check 3: Examine autoscaler logs for errors
echo -e "\n${YELLOW}[3/8] Analyzing autoscaler logs (last 50 lines)...${NC}"
if kubectl logs -n kube-system deployment/cluster-autoscaler --tail=50 2>/dev/null | grep -i "error\|failed\|unable" > /tmp/autoscaler-errors.log; then
    echo -e "${RED}✗ Found errors in autoscaler logs:${NC}"
    head -20 /tmp/autoscaler-errors.log
    echo -e "\n${BLUE}Full error log saved to: /tmp/autoscaler-errors.log${NC}"
else
    echo -e "${GREEN}✓ No recent errors in autoscaler logs${NC}"
fi

# Check 4: Verify IAM/Service Account configuration
echo -e "\n${YELLOW}[4/8] Checking IAM role annotation...${NC}"
IAM_ROLE=$(kubectl get sa cluster-autoscaler -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "NOT_FOUND")
if [[ "$IAM_ROLE" != "NOT_FOUND" ]]; then
    echo -e "${GREEN}✓ IAM role configured: $IAM_ROLE${NC}"
else
    echo -e "${RED}✗ No IAM role annotation found${NC}"
fi

# Check 5: Examine node group configuration
echo -e "\n${YELLOW}[5/8] Checking autoscaler configuration...${NC}"
kubectl logs -n kube-system deployment/cluster-autoscaler --tail=100 2>/dev/null | grep -i "node group\|auto-discovery" | tail -10

# Check 6: Review resource quotas
echo -e "\n${YELLOW}[6/8] Checking resource quotas...${NC}"
QUOTAS=$(kubectl get resourcequota --all-namespaces --no-headers 2>/dev/null | wc -l)
if [[ $QUOTAS -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Found $QUOTAS resource quota(s)${NC}"
    kubectl get resourcequota --all-namespaces
else
    echo -e "${GREEN}✓ No resource quotas configured${NC}"
fi

# Check 7: Check for node selector/affinity issues
echo -e "\n${YELLOW}[7/8] Analyzing unschedulable pod conditions...${NC}"
for pod in $(kubectl get pods --all-namespaces --field-selector=status.phase=Pending -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{"\n"}{end}'); do
    NAMESPACE=$(echo $pod | cut -d'/' -f1)
    POD_NAME=$(echo $pod | cut -d'/' -f2)
    echo -e "\n${BLUE}Pod: $NAMESPACE/$POD_NAME${NC}"
    kubectl describe pod $POD_NAME -n $NAMESPACE 2>/dev/null | grep -A 5 "Events:" | tail -6
done

# Check 8: Get autoscaler metrics
echo -e "\n${YELLOW}[8/8] Fetching autoscaler metrics...${NC}"
kubectl exec -n kube-system deployment/cluster-autoscaler -- wget -q -O- http://localhost:8085/metrics 2>/dev/null | grep -E "cluster_autoscaler_(failed_scale_ups|unschedulable_pods|nodes_count)" || echo "Metrics endpoint unavailable"

echo -e "\n${BLUE}======================================${NC}"
echo -e "${BLUE}Debug Summary Complete${NC}"
echo -e "${BLUE}======================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review autoscaler logs: kubectl logs -n kube-system deployment/cluster-autoscaler -f"
echo "2. Check node group limits in cloud provider console"
echo "3. Verify IAM permissions include: autoscaling:SetDesiredCapacity, ec2:DescribeLaunchTemplateVersions"
echo "4. Examine pod events: kubectl describe pod <pod-name> -n <namespace>"
echo "5. Test with a simple deployment: kubectl create deployment test --image=nginx --replicas=20"
