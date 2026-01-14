# Scenario 4: Volume Mount Permission Denied

## Symptom
MongoDB pod running but logs show `Permission denied` errors when accessing `/data/db`.

## What's Broken
SecurityContext `fsGroup: 1000` doesn't match MongoDB's actual user ID (999). 
Volume is owned by UID 1000, but MongoDB process runs as UID 999.

## Debugging Steps
```bash
# 1. Check pod status and logs
kubectl get pods -n scenario-04
kubectl logs mongodb-0 -n scenario-04 | grep -i permission

# 2. Check security context
kubectl get pod mongodb-0 -n scenario-04 -o jsonpath='{.spec.securityContext}'

# 3. Exec into pod and check permissions
kubectl exec mongodb-0 -n scenario-04 -- ls -la /data/db
kubectl exec mongodb-0 -n scenario-04 -- id

# 4. Check volume mount ownership
kubectl exec mongodb-0 -n scenario-04 -- stat /data/db
```

## Expected Errors
- Logs: `PermissionError: [Errno 13] Permission denied: '/data/db'`
- Logs: `Failed to create directory /data/db/journal`
- Volume owned by `1000:1000` but MongoDB runs as `999:999`

## The Fix
```yaml
securityContext:
  runAsUser: 999  # Match MongoDB's UID
  runAsGroup: 999
  fsGroup: 999  # Critical: Must match container's user
```

## Real-World Context
Stripe's analytics pipeline went down when they upgraded MongoDB images. New version used 
different UID, volumes became unreadable. Fix took 3 hours to identify.

## Time to Debug
Expert: 10 minutes | Intermediate: 30 minutes | Beginner: 90 minutes
