# Scenario 1: PVC Stuck in Pending

## Symptom
PostgreSQL StatefulSet pod stuck in `Pending` state. PVC shows status `Pending`.

## What's Broken
StorageClass name mismatch - PVC requests `fast-ssd` but the actual StorageClass is named `fast-ssd-retain`.

## Debugging Steps
```bash
# 1. Check PVC status
kubectl get pvc -n scenario-01
kubectl describe pvc postgres-data-postgres-0 -n scenario-01

# 2. List available StorageClasses
kubectl get storageclass

# 3. Check events for provisioning errors
kubectl get events -n scenario-01 --sort-by='.lastTimestamp'

# 4. Verify pod status
kubectl get pods -n scenario-01
kubectl describe pod postgres-0 -n scenario-01
```

## Expected Errors
- PVC: `waiting for a volume to be created`
- Event: `storageclass.storage.k8s.io "fast-ssd" not found`

## The Fix
Change `storageClassName: fast-ssd` to `storageClassName: fast-ssd-retain` in the StatefulSet volumeClaimTemplates.

## Real-World Context
This exact issue caused a 6-hour outage at a major e-commerce company during Black Friday 2019. 
Cost: $2.7M in lost revenue. The typo was in a Terraform variable that wasn't caught in staging.

## Time to Debug
Expert: 2 minutes | Intermediate: 10 minutes | Beginner: 30 minutes
