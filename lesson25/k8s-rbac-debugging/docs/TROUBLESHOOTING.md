# Troubleshooting Guide: RBAC Security Misconfigurations

## Common Error Messages and Solutions

### Error: "deployments.apps is forbidden"

**Full error:**
```
Error from server (Forbidden): deployments.apps is forbidden: 
User "system:serviceaccount:ci-cd:deployer" cannot create resource "deployments" 
in API group "apps" in namespace "production"
```

**Diagnosis:**
1. ServiceAccount lacks `create` permission for `deployments.apps` resource
2. Role or RoleBinding likely in wrong namespace
3. Missing RoleBinding entirely

**Solution:**
```bash
# Check if Role exists in target namespace
kubectl get role deployer-role -n production

# If not, apply fixed RBAC
kubectl apply -f k8s/rbac/fixed/
```

### Error: "serviceaccounts 'deployer' not found"

**Cause:** ServiceAccount not created or in wrong namespace

**Solution:**
```bash
# Check ServiceAccount
kubectl get sa -n ci-cd

# Create if missing
kubectl apply -f k8s/rbac/broken/serviceaccount.yaml
```

### Error: Job Pod CrashLoopBackOff

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod -l app=ci-cd-deployer -n ci-cd

# Check logs
kubectl logs -l app=ci-cd-deployer -n ci-cd
```

**Common causes:**
- Image not found (rebuil and reload into cluster)
- Python dependencies missing (check Dockerfile)
- Kubernetes API unreachable (check cluster networking)

### Error: "kubectl: command not found"

**Solution:**
```bash
# Install kubectl
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

## Debugging Workflows

### Workflow 1: Permission Denied Errors

```bash
# Step 1: Identify the exact permission denied
kubectl logs -l app=ci-cd-deployer -n ci-cd | grep "forbidden"

# Step 2: Extract the resource and verb
# Example: "cannot create resource deployments"
# Resource: deployments, Verb: create

# Step 3: Test specific permission
kubectl auth can-i create deployments \
  --as=system:serviceaccount:ci-cd:deployer \
  -n production

# Step 4: Check if Role includes this permission
kubectl describe role deployer-role -n production | grep -A 10 "Rules"

# Step 5: Check if RoleBinding exists
kubectl get rolebinding deployer-binding -n production
```

### Workflow 2: Cross-Namespace Permission Issues

```bash
# Problem: SA in namespace A needs permissions in namespace B

# Step 1: Verify SA exists in source namespace
kubectl get sa deployer -n ci-cd

# Step 2: Check for RoleBindings in target namespace
kubectl get rolebindings -n production -o wide

# Step 3: Ensure Role is in target namespace
kubectl get role deployer-role -n production

# Step 4: Verify RoleBinding references correct SA namespace
kubectl get rolebinding deployer-binding -n production -o yaml | grep namespace
```

### Workflow 3: Missing Subresource Permissions

```bash
# Problem: Can create Deployment but cannot scale it

# Step 1: Check Role for subresource permissions
kubectl describe role deployer-role -n production

# Should see:
# Resources: deployments/scale
# Verbs: update, patch

# Step 2: Test scaling permission specifically
kubectl auth can-i update deployments/scale \
  --as=system:serviceaccount:ci-cd:deployer \
  -n production

# Step 3: Add subresource permission if missing
# Edit Role to include:
# - apiGroups: ["apps"]
#   resources: ["deployments/scale"]
#   verbs: ["update", "patch"]
```

## Advanced Debugging Techniques

### Audit All Permissions for ServiceAccount

```bash
#!/bin/bash
SA="system:serviceaccount:ci-cd:deployer"
NAMESPACE="production"

# Test all common permissions
for resource in deployments services configmaps secrets pods; do
    echo "Testing ${resource}:"
    for verb in create get list update patch delete; do
        result=$(kubectl auth can-i ${verb} ${resource} --as=${SA} -n ${NAMESPACE} 2>&1)
        if [[ $result == "yes" ]]; then
            echo "  ✓ ${verb}"
        else
            echo "  ✗ ${verb}"
        fi
    done
done
```

### Find All RoleBindings for ServiceAccount

```bash
# Search all namespaces
kubectl get rolebindings -A -o json | \
  jq '.items[] | select(.subjects[]?.name=="deployer") | 
    {namespace: .metadata.namespace, name: .metadata.name, role: .roleRef.name}'

# Search ClusterRoleBindings
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.subjects[]?.name=="deployer") | 
    {name: .metadata.name, role: .roleRef.name}'
```

### Compare Broken vs Fixed RBAC

```bash
# Show differences
diff -u k8s/rbac/broken/role.yaml k8s/rbac/fixed/roles.yaml
diff -u k8s/rbac/broken/rolebinding.yaml k8s/rbac/fixed/rolebindings.yaml

# Key differences:
# 1. Namespace: ci-cd → production
# 2. Additional subresource permissions
# 3. More explicit verb lists
```

### Trace API Server Authorization

```bash
# Enable audit logging (if running local cluster)
# For kind:
kind create cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraArgs:
    audit-log-path: /var/log/kubernetes/audit.log
    audit-policy-file: /etc/kubernetes/audit-policy.yaml
