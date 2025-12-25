# Kubernetes RBAC Debugging Lab

## Overview

This lab demonstrates **RBAC security misconfigurations** in Kubernetes through a realistic CI/CD pipeline scenario. You'll learn systematic debugging methodologies used by production engineers at major tech companies to diagnose and fix authorization failures.

### What You'll Learn

- **RBAC Architecture**: Understand ServiceAccounts, Roles, and RoleBindings
- **The Five-Minute Security Drill**: Structured debugging approach for auth failures
- **Namespace-scoped vs Cluster-scoped Permissions**: Critical architectural distinction
- **Production Debugging Patterns**: Real-world troubleshooting techniques
- **kubectl auth can-i**: Testing permissions before deployment

### The Scenario

A CI/CD deployment pipeline fails with "forbidden" errors when trying to deploy applications to production. The ServiceAccount exists, but something in the RBAC configuration prevents it from creating Deployments. Your job: diagnose and fix the security misconfiguration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  ci-cd namespace │        │ production       │          │
│  │                  │        │ namespace        │          │
│  │  ┌────────────┐  │        │                  │          │
│  │  │ deployer   │  │        │  ┌────────────┐  │          │
│  │  │ SA         │───────X───────│ Deployment │  │          │
│  │  └────────────┘  │  (403)  │  └────────────┘  │          │
│  │                  │        │                  │          │
│  │  ┌────────────┐  │        │  ┌────────────┐  │          │
│  │  │ Job Pod    │  │        │  │ Service    │  │          │
│  │  │ (deployer) │  │        │  └────────────┘  │          │
│  │  └────────────┘  │        │                  │          │
│  └──────────────────┘        └──────────────────┘          │
│                                                              │
│  BROKEN: Role & RoleBinding in ci-cd namespace              │
│  FIX: Role & RoleBinding must be in production namespace    │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
k8s-rbac-debugging/
├── app/
│   ├── deployer/              # CI/CD deployment automation
│   │   ├── deployer.py        # Python Kubernetes client
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── sample-app/            # Sample application to deploy
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── k8s/
│   ├── namespaces/            # Namespace definitions
│   │   └── namespaces.yaml
│   ├── rbac/
│   │   ├── broken/            # Intentionally misconfigured RBAC
│   │   │   ├── serviceaccount.yaml
│   │   │   ├── role.yaml
│   │   │   └── rolebinding.yaml
│   │   └── fixed/             # Correct RBAC configuration
│   │       ├── serviceaccount.yaml
│   │       ├── roles.yaml
│   │       └── rolebindings.yaml
│   ├── ci-cd/
│   │   └── deployer-job.yaml # Job that triggers deployment
│   └── applications/
│       └── sample-app.yaml
├── scripts/
│   ├── setup-cluster.sh       # Create local Kubernetes cluster
│   ├── deploy.sh              # Deploy with broken or fixed RBAC
│   ├── cleanup.sh             # Remove all resources
│   └── debugging/
│       ├── diagnose-rbac.sh   # The Five-Minute Security Drill
│       └── test-permissions.sh
└── README.md
```

## Prerequisites

- **Docker** (for building images)
- **kubectl** (Kubernetes CLI)
- **Local Kubernetes cluster**: kind (recommended) or minikube
- **jq** (for JSON parsing in scripts)
- **Python 3.11+** (if running deployer locally)

### Install kind (Recommended)

```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

## Quick Start

### Step 1: Create Kubernetes Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a local kind cluster named `rbac-debugging` with 1 control plane and 2 worker nodes.

### Step 2: Deploy with Broken RBAC

```bash
./scripts/deploy.sh broken
```

**Expected behavior:** The deployment job will fail with a "forbidden" error. This is intentional!

Watch the logs to see the exact permission denial:
```
RBAC PERMISSION DENIED
User "system:serviceaccount:ci-cd:deployer" cannot create resource "deployments"
```

### Step 3: Run the Five-Minute Security Drill

```bash
./scripts/debugging/diagnose-rbac.sh
```

This script executes a systematic debugging methodology:

1. **Verify the Failure**: Confirm the job failed
2. **Audit ServiceAccount**: Check if SA exists
3. **Find RoleBindings**: Search for ALL bindings referencing the SA
4. **Inspect Roles**: Examine Role permissions and namespace
5. **Test Permissions**: Use `kubectl auth can-i` to verify

**Expected output:** The script identifies:
- Role exists in `ci-cd` namespace (WRONG)
- RoleBinding exists in `ci-cd` namespace (WRONG)
- No permissions granted in `production` namespace

### Step 4: Apply the Fix

```bash
./scripts/deploy.sh fixed
```

This applies the corrected RBAC configuration:
- Role created in `production` namespace
- RoleBinding created in `production` namespace
- Proper permissions for deployment automation

**Expected behavior:** Deployment succeeds! 🎉

Verify resources were created:
```bash
kubectl get deployments,services,pods -n production
```

## Understanding the Issue

### The Problem: Namespace-Scoped Permissions

**Roles are namespace-scoped.** A Role defined in namespace A cannot grant permissions in namespace B.

#### Broken Configuration

```yaml
# WRONG: Role in ci-cd namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: ci-cd  # ❌ Wrong namespace
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create"]
---
# WRONG: RoleBinding in ci-cd namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: ci-cd  # ❌ Wrong namespace
roleRef:
  kind: Role
  name: deployer-role
subjects:
- kind: ServiceAccount
  name: deployer
  namespace: ci-cd
```

**Why this fails:** The deployer tries to create a Deployment in `production` namespace, but the Role only grants permissions within `ci-cd` namespace.

#### Fixed Configuration

```yaml
# CORRECT: Role in production namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: production  # ✅ Correct namespace
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "update"]
---
# CORRECT: RoleBinding in production namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: production  # ✅ Correct namespace
roleRef:
  kind: Role
  name: deployer-role
subjects:
- kind: ServiceAccount
  name: deployer
  namespace: ci-cd  # ✅ SA can be in different namespace
```

**Key insight:** ServiceAccounts can be in a different namespace from their RoleBindings. The RoleBinding must be in the namespace where permissions are needed.

## The Five-Minute Security Drill

When facing RBAC failures, follow this systematic approach:

### 1. Reproduce the Failure (60 seconds)

Capture the exact error message. Look for:
- Forbidden resource (e.g., `deployments`)
- Verb attempted (e.g., `create`)
- ServiceAccount identity (e.g., `system:serviceaccount:ci-cd:deployer`)

### 2. Audit ServiceAccount Bindings (90 seconds)

```bash
# Find ALL bindings for the ServiceAccount
kubectl get rolebindings,clusterrolebindings --all-namespaces -o json | \
  jq '.items[] | select(.subjects[]?.name=="deployer")'

# Check bindings in target namespace specifically
kubectl get rolebindings -n production -o wide
```

**Common mistake:** Only checking the ServiceAccount's home namespace.

### 3. Test Permissions (30 seconds)

```bash
# Simulate the API server's authorization check
kubectl auth can-i create deployments \
  --as=system:serviceaccount:ci-cd:deployer \
  -n production
```

Returns `yes` if allowed, `no` if denied.

### 4. Inspect Role Permissions (90 seconds)

```bash
# Check if Role exists in target namespace
kubectl get role deployer-role -n production

# Describe the Role to see permissions
kubectl describe role deployer-role -n production
```

Look for:
- Correct API group (`apps` for Deployments)
- Correct resource (`deployments`)
- Correct verbs (`create`, `get`, `list`, etc.)

### 5. Implement the Fix (90 seconds)

Create or update the Role and RoleBinding in the correct namespace.

```bash
# Apply fixed configuration
kubectl apply -f k8s/rbac/fixed/

# Re-test permission
kubectl auth can-i create deployments \
  --as=system:serviceaccount:ci-cd:deployer \
  -n production
```

## Manual Testing

### Test Individual Permissions

```bash
./scripts/debugging/test-permissions.sh
```

This tests all common permissions the deployer needs:
- Deployment creation/reading/updating
- Service management
- ConfigMap access
- Secret reading
- Pod status checking

### Inspect RBAC Resources

```bash
# View ServiceAccount
kubectl get sa deployer -n ci-cd -o yaml

# View all RoleBindings in production
kubectl get rolebindings -n production

# Describe specific Role
kubectl describe role deployer-role -n production

# List all Roles and RoleBindings
kubectl get roles,rolebindings --all-namespaces
```

### Check Job and Pod Status

```bash
# View job status
kubectl get job deployment-job -n ci-cd

# Get pod logs
POD=$(kubectl get pods -n ci-cd -l app=ci-cd-deployer -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD -n ci-cd
```

## Common RBAC Mistakes

### 1. Role in Wrong Namespace

❌ **Wrong:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: ci-cd  # SA's home namespace
```

✅ **Correct:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: production  # Target namespace
```

### 2. Missing Subresource Permissions

❌ **Wrong:**
```yaml
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get"]
  # Missing: deployments/scale, deployments/status
```

✅ **Correct:**
```yaml
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments/scale"]  # Subresource
  verbs: ["get", "update", "patch"]
```

### 3. Using ClusterRole When Not Needed

❌ **Excessive:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole  # Grants cluster-wide permissions
metadata:
  name: deployer-role
```

✅ **Least Privilege:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role  # Namespace-scoped
metadata:
  name: deployer-role
  namespace: production
```

**Use ClusterRole only when you need cluster-wide permissions** (e.g., for operators managing resources across all namespaces).

### 4. Wildcard Verbs Without Security Review

❌ **Dangerous:**
```yaml
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]  # Full cluster admin
```

✅ **Explicit:**
```yaml
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "update", "patch"]
  # Explicitly list only required permissions
```

## Production Best Practices

### 1. Least Privilege Principle

Grant only the minimum permissions needed:

```yaml
# Deployer needs create but not delete
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "update"]  # No 'delete'
```

### 2. Namespace-Scoped by Default

Use Roles instead of ClusterRoles unless absolutely necessary:

```yaml
# Good: Namespace-scoped
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production

# Use ClusterRole only for cluster-wide operators
```

### 3. Separate ServiceAccounts per Function

Don't reuse ServiceAccounts across different functions:

```yaml
# Separate SAs for different responsibilities
- CI/CD deployer SA
- Monitoring SA
- Backup SA
```

### 4. Document Permission Requirements

Include RBAC documentation in deployment guides:

```yaml
# Required permissions for this application:
# - create/get/list deployments
# - create/get services
# - get secrets (read-only)
```

### 5. Automated RBAC Audits

Implement periodic audits for unused or excessive permissions:

```bash
# Find ServiceAccounts with >10 RoleBindings
kubectl get rolebindings -A -o json | \
  jq '.items | group_by(.subjects[].name) | .[] | select(length > 10)'
```

### 6. Break-Glass Patterns

Pre-create emergency admin access that's only activated during incidents:

```yaml
# Emergency break-glass role (kept dormant)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: incident-response
  annotations:
    usage: "Only for production incidents"
```

## Troubleshooting

### Issue: Job Succeeds with Broken RBAC

**Possible cause:** You previously applied the fixed RBAC configuration.

**Solution:**
```bash
./scripts/cleanup.sh
./scripts/deploy.sh broken
```

### Issue: Cannot Connect to Cluster

**Solution:**
```bash
# Check cluster status
kubectl cluster-info

# If using kind
kind get clusters

# If using minikube
minikube status
```

### Issue: Images Not Found

**Solution:**
```bash
# Rebuild images
docker build -t deployer:latest app/deployer/
docker build -t sample-app:latest app/sample-app/

# Reload into kind cluster
kind load docker-image deployer:latest
kind load docker-image sample-app:latest
```

### Issue: Permission Denied Even with Fixed RBAC

**Check:**
1. Role and RoleBinding are in correct namespace (`production`)
2. ServiceAccount name matches in RoleBinding subjects
3. Role includes all required resources and verbs
4. Test with `kubectl auth can-i`

```bash
kubectl auth can-i create deployments \
  --as=system:serviceaccount:ci-cd:deployer -n production
```

## Learning Extensions

### 1. Add Staging Environment

Extend the deployer to support multiple environments:

```bash
# Deploy to staging
kubectl set env job/deployment-job TARGET_NAMESPACE=staging -n ci-cd
```

Create RBAC in staging namespace following the same pattern.

### 2. Implement Multi-Tenant RBAC

Create separate namespaces for different teams with isolated RBAC:

```yaml
# Team A namespace with dedicated ServiceAccount
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: team-a-deployer
  namespace: team-a
```

### 3. Add ClusterRole for Cluster-Wide Operations

Some operations require cluster-wide permissions:

```yaml
# Cluster-wide read-only monitoring
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-reader
rules:
- apiGroups: [""]
  resources: ["nodes", "persistentvolumes"]
  verbs: ["get", "list", "watch"]
```

### 4. Implement RBAC Policy as Code

Store all RBAC in Git with mandatory review process:

```bash
# Pre-commit hook to validate RBAC
./scripts/validate-rbac.sh

# CI check for overly permissive roles
grep -r "verbs: \[\"\*\"\]" k8s/rbac/ && exit 1
```

## Scale Connection: RBAC at FAANG

### Google (GKE)

- 100,000+ ServiceAccounts across customer clusters
- Every ServiceAccount defined in GitOps manifests
- Mandatory security review for cluster-admin bindings
- Automated RBAC validators in CI

### Uber

- Built RBAC validators rejecting wildcard verbs without approval
- Platform team maintains pre-approved RBAC templates
- Quarterly audits flagging ServiceAccounts with >10 bindings

### Datadog

- "Deployment runner" and "monitoring operator" RBAC templates
- Least privilege enforced through automated policy checks
- ServiceAccounts scoped to single function

### Shopify

- Automated RBAC drift detection
- Flags excess permissions from deleted features
- Break-glass incident-response ClusterRoles for emergencies

## Cleanup

Remove all resources:

```bash
./scripts/cleanup.sh
```

Delete the cluster:

```bash
# If using kind
kind delete cluster --name rbac-debugging

# If using minikube
minikube delete
```

## Key Takeaways

1. **Roles are namespace-scoped** - Create them in the target namespace
2. **RoleBindings grant permissions in their namespace** - Not the ServiceAccount's namespace
3. **ServiceAccounts can cross namespaces** - SA in `ci-cd` can have bindings in `production`
4. **Test before deploying** - Always use `kubectl auth can-i`
5. **Systematic debugging** - Follow the Five-Minute Security Drill
6. **Least privilege** - Grant minimum necessary permissions
7. **Document RBAC requirements** - Make permission needs explicit

## References

- [Kubernetes RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [kubectl auth can-i](https://kubernetes.io/docs/reference/access-authn-authz/authorization/#checking-api-access)
- [ServiceAccounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/security-best-practices/)

---

**Next Steps:** Apply these debugging patterns to your own Kubernetes security configurations. Master RBAC troubleshooting, and you'll handle 95% of auth failures in under five minutes.
