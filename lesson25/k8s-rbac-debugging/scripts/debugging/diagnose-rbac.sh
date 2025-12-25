#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}          THE FIVE-MINUTE RBAC SECURITY DRILL                        ${NC}"
echo -e "${GREEN}======================================================================${NC}"

SA_NAME="deployer"
SA_NAMESPACE="ci-cd"
TARGET_NAMESPACE="production"

echo -e "\n${BLUE}[Step 1: Verify the Failure]${NC}"
echo -e "${YELLOW}Checking if deployment job failed...${NC}"

JOB_STATUS=$(kubectl get job deployment-job -n ci-cd -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "NotFound")

if [ "${JOB_STATUS}" = "Failed" ]; then
    echo -e "${RED}✗ Job failed (expected with broken RBAC)${NC}"
    
    POD_NAME=$(kubectl get pods -n ci-cd -l app=ci-cd-deployer --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
    echo -e "\n${YELLOW}Error from pod logs:${NC}"
    kubectl logs "${POD_NAME}" -n ci-cd | grep -A 5 "RBAC PERMISSION DENIED" || echo "No RBAC error found"
elif [ "${JOB_STATUS}" = "Complete" ]; then
    echo -e "${GREEN}✓ Job completed successfully${NC}"
    echo -e "${YELLOW}RBAC appears to be correctly configured${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Job status: ${JOB_STATUS}${NC}"
fi

echo -e "\n${BLUE}[Step 2: Audit ServiceAccount]${NC}"
echo -e "${YELLOW}Checking ServiceAccount '${SA_NAME}' in namespace '${SA_NAMESPACE}'...${NC}"

if kubectl get sa "${SA_NAME}" -n "${SA_NAMESPACE}" &> /dev/null; then
    echo -e "${GREEN}✓ ServiceAccount exists${NC}"
    kubectl get sa "${SA_NAME}" -n "${SA_NAMESPACE}"
else
    echo -e "${RED}✗ ServiceAccount not found${NC}"
    exit 1
fi

echo -e "\n${BLUE}[Step 3: Find All RoleBindings for ServiceAccount]${NC}"
echo -e "${YELLOW}Searching for RoleBindings referencing '${SA_NAME}'...${NC}\n"

echo -e "${YELLOW}RoleBindings in ${SA_NAMESPACE}:${NC}"
kubectl get rolebindings -n "${SA_NAMESPACE}" -o json | \
    jq -r '.items[] | select(.subjects[]?.name=="'${SA_NAME}'") | "  • \(.metadata.name) → \(.roleRef.kind)/\(.roleRef.name)"' || echo "  None found"

echo -e "\n${YELLOW}RoleBindings in ${TARGET_NAMESPACE}:${NC}"
kubectl get rolebindings -n "${TARGET_NAMESPACE}" -o json | \
    jq -r '.items[] | select(.subjects[]?.name=="'${SA_NAME}'") | "  • \(.metadata.name) → \(.roleRef.kind)/\(.roleRef.name)"' || echo "  None found"

echo -e "\n${YELLOW}ClusterRoleBindings:${NC}"
kubectl get clusterrolebindings -o json | \
    jq -r '.items[] | select(.subjects[]?.name=="'${SA_NAME}'") | "  • \(.metadata.name) → \(.roleRef.kind)/\(.roleRef.name)"' || echo "  None found"

echo -e "\n${RED}🔍 KEY FINDING:${NC}"
PROD_BINDINGS=$(kubectl get rolebindings -n "${TARGET_NAMESPACE}" -o json | jq -r '.items[] | select(.subjects[]?.name=="'${SA_NAME}'") | .metadata.name' | wc -l)
if [ "${PROD_BINDINGS}" -eq 0 ]; then
    echo -e "${RED}✗ No RoleBindings found in target namespace '${TARGET_NAMESPACE}'${NC}"
    echo -e "${RED}  This is the problem! ServiceAccount needs permissions in the namespace where it deploys.${NC}"
else
    echo -e "${GREEN}✓ RoleBindings exist in target namespace${NC}"
fi

echo -e "\n${BLUE}[Step 4: Inspect Role Permissions]${NC}"
echo -e "${YELLOW}Checking Role 'deployer-role' permissions...${NC}\n"

echo -e "${YELLOW}In ci-cd namespace:${NC}"
if kubectl get role deployer-role -n ci-cd &> /dev/null; then
    echo -e "${YELLOW}Role exists in ci-cd namespace, but this is WRONG!${NC}"
    echo -e "${RED}Roles are namespace-scoped. A Role in 'ci-cd' cannot grant permissions in 'production'${NC}"
    kubectl describe role deployer-role -n ci-cd | grep -A 20 "Rules:" || echo "  (No rules section found)"
else
    echo -e "${GREEN}No role in ci-cd namespace (correct)${NC}"
fi

echo -e "\n${YELLOW}In production namespace:${NC}"
if kubectl get role deployer-role -n production &> /dev/null; then
    echo -e "${GREEN}✓ Role exists in production namespace${NC}"
    kubectl describe role deployer-role -n production | grep -A 30 "Rules:" || echo "  (No rules section found)"
else
    echo -e "${RED}✗ No role in production namespace${NC}"
    echo -e "${RED}  Role must be created in the namespace where permissions are needed!${NC}"
fi

echo -e "\n${BLUE}[Step 5: Test Permissions with auth can-i]${NC}"
echo -e "${YELLOW}Testing specific permissions for ServiceAccount...${NC}\n"

SA_FULL_NAME="system:serviceaccount:${SA_NAMESPACE}:${SA_NAME}"

# Test various permissions
declare -A permissions=(
    ["create deployments"]="create"
    ["get deployments"]="get"
    ["list deployments"]="list"
    ["update deployments"]="update"
    ["create services"]="create"
    ["get secrets"]="get"
)

for perm in "${!permissions[@]}"; do
    verb="${permissions[$perm]}"
    resource="${perm#* }"
    
    if kubectl auth can-i "${verb}" "${resource}" --as="${SA_FULL_NAME}" -n "${TARGET_NAMESPACE}" 2>/dev/null; then
        echo -e "${GREEN}✓ Can ${perm}${NC}"
    else
        echo -e "${RED}✗ Cannot ${perm}${NC}"
    fi
done

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}                    DIAGNOSIS SUMMARY                                ${NC}"
echo -e "${GREEN}======================================================================${NC}"

echo -e "\n${YELLOW}Common RBAC Issues Detected:${NC}\n"

# Check 1: Role in wrong namespace
if kubectl get role deployer-role -n ci-cd &> /dev/null && ! kubectl get role deployer-role -n production &> /dev/null; then
    echo -e "${RED}[Issue 1] Role defined in wrong namespace${NC}"
    echo -e "  Problem: Role exists in 'ci-cd' but should be in 'production'"
    echo -e "  Impact: Cannot grant permissions in production namespace"
    echo -e "  Fix: Create Role in production namespace"
fi

# Check 2: RoleBinding in wrong namespace
if kubectl get rolebinding deployer-binding -n ci-cd &> /dev/null && [ "${PROD_BINDINGS}" -eq 0 ]; then
    echo -e "\n${RED}[Issue 2] RoleBinding in wrong namespace${NC}"
    echo -e "  Problem: RoleBinding exists in 'ci-cd' but should be in 'production'"
    echo -e "  Impact: Binding doesn't grant permissions in target namespace"
    echo -e "  Fix: Create RoleBinding in production namespace"
fi

# Check 3: Missing permissions
if ! kubectl auth can-i create deployments --as="${SA_FULL_NAME}" -n "${TARGET_NAMESPACE}" 2>/dev/null; then
    echo -e "\n${RED}[Issue 3] Missing create deployments permission${NC}"
    echo -e "  Problem: ServiceAccount cannot create deployments"
    echo -e "  Impact: Deployment automation fails"
    echo -e "  Fix: Add 'create' verb for 'deployments' resource in Role"
fi

echo -e "\n${YELLOW}Recommended Fix:${NC}"
echo -e "  1. Delete broken RBAC: kubectl delete -f k8s/rbac/broken/"
echo -e "  2. Apply fixed RBAC: kubectl apply -f k8s/rbac/fixed/"
echo -e "  3. Re-run deployment: ./scripts/deploy.sh fixed"

echo -e "\n${BLUE}Learning Points:${NC}"
echo -e "  • Roles are namespace-scoped - create them in the target namespace"
echo -e "  • RoleBindings must be in the namespace where permissions are granted"
echo -e "  • ServiceAccounts can be in different namespaces from their bindings"
echo -e "  • Always test with 'kubectl auth can-i' before deploying"

echo -e "\n${GREEN}======================================================================${NC}"
