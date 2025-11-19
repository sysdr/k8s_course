# Lesson 10: Break-It-Friday - K8s Scheduling & Networking Debug Lab

A hands-on debugging laboratory with intentionally broken Kubernetes deployments for practicing production troubleshooting skills.

## Quick Start

```bash
# 1. Setup local cluster
./scripts/setup-cluster.sh

# 2. Deploy broken scenarios
./scripts/deploy-broken.sh

# 3. Run diagnostic helper
./scripts/debug-helper.sh

# 4. Fix issues and verify
kubectl get pods -n log-processor
```

## Debugging Scenarios

### Scheduling Failures

| Scenario | Issue | Debug Command |
|----------|-------|---------------|
| Resource Exhaustion | CPU request exceeds node capacity | `kubectl describe pod log-ingester-xxx -n log-processor` |
| Affinity Mismatch | Required node labels don't exist | `kubectl get nodes --show-labels \| grep gpu` |
| Taint/Toleration | Untolerated node taint | `kubectl describe nodes \| grep Taints` |
| Missing StorageClass | PVC references non-existent SC | `kubectl get sc; kubectl describe pvc -n log-processor` |
| Quota Exceeded | ResourceQuota exhausted | `kubectl describe resourcequota -n log-processor` |

### Networking Failures

| Scenario | Issue | Debug Command |
|----------|-------|---------------|
| Selector Mismatch | Service selector doesn't match Pods | `kubectl get endpoints log-api -n log-processor` |
| DNS Blocked | NetworkPolicy blocks DNS queries | `kubectl exec -it <pod> -- nslookup kubernetes` |
| Port Mismatch | Service targetPort wrong | `kubectl describe svc log-processor -n log-processor` |
| Missing Backend | Ingress references missing Service | `kubectl describe ingress log-ingress -n log-processor` |

## Debugging Workflow

### 1. Identify the Symptom

```bash
# Check for Pending/Error Pods
kubectl get pods -n log-processor | grep -E "Pending|Error|CrashLoop"

# Check recent events
kubectl get events -n log-processor --sort-by='.lastTimestamp' | tail -20
```

### 2. Gather Details

```bash
# For Pending Pods - check scheduler message
kubectl describe pod <pod-name> -n log-processor | grep -A 10 "Events:"

# For networking issues - check endpoints
kubectl get endpoints -n log-processor
```

### 3. Identify Root Cause

- **"Insufficient cpu"** → Resource request too high
- **"node(s) had untolerated taint"** → Missing toleration
- **"no matching node"** → Affinity/selector mismatch
- **Empty endpoints** → Service selector mismatch
- **DNS resolution failed** → NetworkPolicy blocking egress

### 4. Apply Fix

```bash
# Apply individual solution
./scripts/apply-solutions.sh 1

# Or apply all solutions
./scripts/apply-solutions.sh all
```

## Project Structure

```
k8s-debug-lab/
├── k8s/
│   ├── base/                    # Namespace and common resources
│   ├── broken-scheduling/       # Scheduling failure scenarios
│   ├── broken-networking/       # Networking failure scenarios
│   └── solutions/               # Fixed manifests
├── services/                    # Python microservices
│   ├── log-ingester/
│   ├── log-processor/
│   ├── log-api/
│   └── log-dashboard/
├── scripts/
│   ├── setup-cluster.sh         # Create kind cluster
│   ├── deploy-broken.sh         # Deploy broken scenarios
│   ├── debug-helper.sh          # Diagnostic tool
│   ├── apply-solutions.sh       # Apply fixes
│   └── cleanup.sh               # Cleanup resources
└── docs/
    └── debugging-cheatsheet.md
```

## Key Commands Reference

```bash
# Pod debugging
kubectl describe pod <pod> -n log-processor
kubectl logs <pod> -n log-processor
kubectl exec -it <pod> -n log-processor -- /bin/sh

# Scheduling debugging
kubectl get events --field-selector=reason=FailedScheduling
kubectl top nodes
kubectl describe node <node> | grep -A 5 "Allocated resources"

# Networking debugging
kubectl get endpoints <service> -n log-processor
kubectl run test --rm -it --image=busybox -- nslookup <service>.log-processor
kubectl get networkpolicies -n log-processor -o yaml

# Resource debugging
kubectl describe resourcequota -n log-processor
kubectl get pvc -n log-processor
kubectl get sc
```

## Learning Objectives

After completing this lab, you should be able to:

1. Diagnose why Pods are stuck in Pending state
2. Identify and resolve node affinity/taint issues
3. Debug Service endpoint discovery problems
4. Understand NetworkPolicy impact on DNS resolution
5. Use kubectl effectively for production troubleshooting

## Cleanup

```bash
# Remove namespace only
./scripts/cleanup.sh

# Remove namespace and cluster
./scripts/cleanup.sh --full
```
