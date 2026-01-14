# Scenario 3: PostgreSQL CrashLoopBackOff

## Symptom
PostgreSQL pod in `CrashLoopBackOff`. Logs show OOMKilled or rapid restarts.

## What's Broken
Two issues:
1. Memory limit (128Mi) too low for PostgreSQL initialization (needs ~256Mi minimum)
2. Readiness probe kills pod before database finishes starting (needs 30s+ initialDelay)

## Debugging Steps
```bash
# 1. Check pod status
kubectl get pods -n scenario-03
kubectl describe pod postgres-0 -n scenario-03

# 2. Check logs for OOMKilled
kubectl logs postgres-0 -n scenario-03 --previous

# 3. Check events for memory/probe failures
kubectl get events -n scenario-03 | grep -i "killed\|oom\|readiness"

# 4. Check resource limits
kubectl get pod postgres-0 -n scenario-03 -o jsonpath='{.spec.containers[0].resources}'

# 5. Monitor live startup
kubectl logs postgres-0 -n scenario-03 -f
```

## Expected Errors
- Pod: `OOMKilled` or `CrashLoopBackOff`
- Logs: `Postgres killed by signal 9` or `Readiness probe failed`
- Events: `Back-off restarting failed container`

## The Fix
```yaml
resources:
  requests:
    memory: "256Mi"  # Adequate for initialization
    cpu: "250m"
  limits:
    memory: "512Mi"  # Room for growth
    cpu: "500m"
readinessProbe:
  initialDelaySeconds: 30  # Allow full initialization
  periodSeconds: 10
  failureThreshold: 6  # More tolerant
```

## Real-World Context
Airbnb's payment database went down for 2 hours because someone "optimized" memory limits 
without testing startup time. PostgreSQL kept OOMKilling during initialization.

## Time to Debug
Expert: 5 minutes | Intermediate: 20 minutes | Beginner: 60 minutes
