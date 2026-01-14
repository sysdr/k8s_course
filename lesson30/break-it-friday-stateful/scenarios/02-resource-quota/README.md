# Scenario 2: Resource Quota Preventing PVC Creation

## Symptom
MySQL StatefulSet creates first 2 pods successfully, but pod #3 stuck in `Pending`.

## What's Broken
ResourceQuota allows only 2 PVCs and 5Gi total storage, but StatefulSet requires 3 PVCs with 15Gi total.

## Debugging Steps
```bash
# 1. Check StatefulSet status
kubectl get statefulset -n scenario-02
kubectl describe sts mysql-cluster -n scenario-02

# 2. Check PVC status
kubectl get pvc -n scenario-02

# 3. Check ResourceQuota
kubectl get resourcequota -n scenario-02
kubectl describe quota storage-quota -n scenario-02

# 4. Check pod events
kubectl get events -n scenario-02 --sort-by='.lastTimestamp' | grep -i quota
```

## Expected Errors
- PVC: `exceeded quota: storage-quota`
- StatefulSet: `create Pod mysql-cluster-2: forbidden: exceeded quota`

## The Fix
Increase ResourceQuota limits:
```yaml
spec:
  hard:
    requests.storage: "20Gi"  # Allow 15Gi + buffer
    persistentvolumeclaims: "5"  # Allow 3 + buffer
```

## Real-World Context
Capital One discovered this issue when a team expanded their database cluster from 3 to 5 replicas. 
The new pods never started, causing split-brain scenarios and data inconsistency.

## Time to Debug
Expert: 3 minutes | Intermediate: 15 minutes | Beginner: 45 minutes
