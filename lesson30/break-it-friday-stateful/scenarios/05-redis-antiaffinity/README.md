# Scenario 5: Redis Split-Brain from Anti-Affinity

## Symptom
Redis StatefulSet only deploys 3 pods successfully. Pods 4 and 5 stuck in `Pending`.

## What's Broken
Anti-affinity uses `requiredDuringSchedulingIgnoredDuringExecution` which mandates one pod 
per node. With 5 replicas but only 3 nodes, 2 pods can never schedule.

## Debugging Steps
```bash
# 1. Check StatefulSet and pod status
kubectl get statefulset -n scenario-05
kubectl get pods -n scenario-05

# 2. Describe pending pods
kubectl describe pod redis-3 -n scenario-05
kubectl describe pod redis-4 -n scenario-05

# 3. Check anti-affinity rules
kubectl get sts redis -n scenario-05 -o jsonpath='{.spec.template.spec.affinity}'

# 4. Count available nodes
kubectl get nodes
kubectl describe nodes | grep -A 5 "Non-terminated Pods"
```

## Expected Errors
- Pods: `0/3 nodes are available: 3 node(s) didn't match pod anti-affinity rules`
- Event: `FailedScheduling: no nodes available matching pod anti-affinity`

## The Fix
Use `preferredDuringSchedulingIgnoredDuringExecution` instead:
```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:  # Soft constraint
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: redis
        topologyKey: kubernetes.io/hostname
```

## Real-World Context
Netflix's caching layer failed during a node outage. Anti-affinity was so strict that 
replacement pods couldn't schedule, causing cascading failures across services.

## Time to Debug
Expert: 5 minutes | Intermediate: 20 minutes | Beginner: 60 minutes
