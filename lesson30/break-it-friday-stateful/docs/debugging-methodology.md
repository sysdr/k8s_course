# Systematic Stateful Application Debugging Methodology

## Overview

This document outlines the proven debugging methodology used by SRE teams at Netflix, Datadog, Stripe, and other major tech companies when diagnosing stateful application failures in Kubernetes.

## The Five-Minute Drill

### Purpose
Quickly isolate the layer where failure is occurring:
1. Storage provisioning layer (StorageClass, cloud provider)
2. Volume binding layer (PVC to PV attachment)
3. Pod scheduling layer (node capacity, affinity rules)
4. Volume attachment layer (mount, permissions)
5. Application layer (database startup, configuration)

### Minute 1: Verify Storage Stack

**Goal**: Confirm StorageClass configuration and availability

```bash
# List all PVCs and their status
kubectl get pvc -n <namespace>

# Detailed PVC information
kubectl describe pvc <pvc-name> -n <namespace>

# Check all StorageClasses
kubectl get storageclass

# Verify specific StorageClass details
kubectl get storageclass <name> -o yaml
```

**Common Issues**:
- StorageClass doesn't exist (typo in name)
- No default StorageClass when none specified
- Wrong provisioner configured
- Missing required parameters

**Red Flags**:
- Event: `storageclass.storage.k8s.io "xyz" not found`
- Event: `no default storageclass found`
- PVC Status: `Pending` for > 2 minutes

### Minute 2: Inspect Volume Binding

**Goal**: Verify PV provisioning and binding

```bash
# List all PersistentVolumes
kubectl get pv

# Filter PVs by StorageClass
kubectl get pv -o wide | grep <storageclass>

# Detailed PV information
kubectl describe pv <pv-name>

# Check resource quotas
kubectl get resourcequota -A
kubectl describe quota <quota-name> -n <namespace>
```

**Common Issues**:
- PV provisioning timeout (cloud provider issues)
- Resource quota exceeded (storage or PVC count)
- Cloud provider quota limits (EBS volumes, GCE disks)
- Insufficient node capacity

**Red Flags**:
- Event: `quota exceeded`
- Event: `timeout waiting for volume to be created`
- No PV bound to PVC after 5 minutes

### Minute 3: Validate Pod-Volume Attachment

**Goal**: Confirm pod can attach and mount volumes

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n <namespace>

# View volume specs
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.volumes}'

# Check volume mounts
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].volumeMounts}'

# Check node capacity
kubectl describe node <node-name> | grep -A 5 "Allocated resources"

# Volume attachment limit (AWS: 39, GCP: 128)
kubectl describe node <node-name> | grep -i volumes
```

**Common Issues**:
- Node at volume attachment limit
- Mount path conflicts
- Volume already attached to different node
- Volume type not supported on node

**Red Flags**:
- Event: `AttachVolume.Attach failed`
- Event: `Volume is already attached to node`
- Event: `max volume count exceeded`

### Minute 4: Examine StatefulSet Ordering

**Goal**: Understand StatefulSet deployment state

```bash
# StatefulSet status
kubectl get statefulset -n <namespace>
kubectl describe sts <name> -n <namespace>

# Check pod management policy
kubectl get sts <name> -o jsonpath='{.spec.podManagementPolicy}'

# Check update strategy
kubectl get sts <name> -o jsonpath='{.spec.updateStrategy}'

# View replicas status
kubectl get sts <name> -o jsonpath='{.status}'
```

**Common Issues**:
- Pod N stuck because Pod N-1 not Ready
- Volume claim template mismatch
- Anti-affinity preventing scheduling
- PodDisruptionBudget blocking updates

**Red Flags**:
- Ready replicas < Desired replicas
- Pods stuck in same order (0, 1 OK; 2 stuck)
- Update stuck at partition value

### Minute 5: Analyze Application State

**Goal**: Verify application-level health and data integrity

```bash
# Check current and previous logs
kubectl logs <pod-name> -n <namespace> --tail=100
kubectl logs <pod-name> -n <namespace> --previous

# Check disk usage in pod
kubectl exec <pod-name> -n <namespace> -- df -h

# Check data directory
kubectl exec <pod-name> -n <namespace> -- ls -la /var/lib/<app>

# Check for lock files
kubectl exec <pod-name> -n <namespace> -- find /var/lib/<app> -name "*.lock"

# Check process status
kubectl exec <pod-name> -n <namespace> -- ps aux
```

**Common Issues**:
- Disk full
- Corrupt data files
- Lock files from unclean shutdown
- Insufficient memory (OOMKilled)
- Permission denied errors

**Red Flags**:
- Logs: `No space left on device`
- Logs: `Permission denied`
- Logs: `Killed by signal 9` (OOM)
- Logs: `database recovery mode`

## Extended Debugging Techniques

### Deep Dive: PVC Pending

When PVC stuck in Pending after 5-minute drill:

```bash
# 1. Check StorageClass provisioner logs
kubectl logs -n kube-system -l app=csi-driver --tail=50

# 2. Check dynamic provisioner events
kubectl get events -n <namespace> --field-selector involvedObject.kind=PersistentVolumeClaim

# 3. Verify RBAC for provisioner
kubectl auth can-i create persistentvolumes --as=system:serviceaccount:kube-system:persistent-volume-binder

# 4. Check cloud provider status (AWS example)
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/created-for/pvc/name,Values=<pvc-name>"

# 5. Manual PV creation (last resort)
cat <<MANUAL_PV_EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: manual-pv-<pvc-name>
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  claimRef:
    name: <pvc-name>
    namespace: <namespace>
  hostPath:
    path: /mnt/data
MANUAL_PV_EOF
```

### Deep Dive: CrashLoopBackOff

When pod repeatedly crashes:

```bash
# 1. Check exit code
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'

# 2. Check for OOMKilled
kubectl describe pod <pod-name> -n <namespace> | grep -i oom

# 3. Get full logs from crashed container
kubectl logs <pod-name> -n <namespace> --previous --tail=-1

# 4. Check resource limits
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].resources}'

# 5. Temporarily increase resources
kubectl patch sts <name> -n <namespace> --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "1Gi"}]'

# 6. Check probe configuration
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].livenessProbe}'
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].readinessProbe}'
```

### Deep Dive: Permission Denied

When volume mount fails due to permissions:

```bash
# 1. Check pod security context
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.securityContext}'

# 2. Check container user
kubectl exec <pod-name> -n <namespace> -- id

# 3. Check volume ownership
kubectl exec <pod-name> -n <namespace> -- stat /mount/path

# 4. Check SELinux labels (if applicable)
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.securityContext.seLinuxOptions}'

# 5. Temporarily run as root for debugging
kubectl patch sts <name> -n <namespace> --type='json' -p='[{"op": "add", "path": "/spec/template/spec/securityContext/runAsUser", "value": 0}]'

# 6. Fix ownership
kubectl exec <pod-name> -n <namespace> -- chown -R <uid>:<gid> /mount/path
```

## Debugging Decision Tree

```
PVC Pending?
├── Yes
│   ├── StorageClass exists?
│   │   ├── No → Fix StorageClass name
│   │   └── Yes → Check quota
│   └── Check quota exceeded?
│       ├── Yes → Increase quota
│       └── No → Check provisioner logs
└── No (PVC Bound)
    └── Pod Pending?
        ├── Yes
        │   ├── Check node capacity
        │   ├── Check affinity rules
        │   └── Check volume attachment limits
        └── No (Pod Running)
            └── Pod CrashLoop?
                ├── Yes
                │   ├── Check logs for OOM
                │   ├── Check probe timing
                │   └── Check disk space
                └── No → Check application logs
```

## Common Anti-Patterns

### 1. Implicit StorageClass Reliance
**Problem**: Not specifying `storageClassName`  
**Impact**: Breaks when default changes  
**Fix**: Always specify explicitly

### 2. Tight Resource Limits
**Problem**: Memory/CPU too low for startup  
**Impact**: Constant restarts during initialization  
**Fix**: Allow 2x startup resources, tighten after warmup

### 3. Aggressive Probe Timing
**Problem**: `initialDelaySeconds` < actual startup time  
**Impact**: Pod killed before ready  
**Fix**: Set initialDelay to 1.5x typical startup time

### 4. Required Anti-Affinity
**Problem**: Using `required` instead of `preferred`  
**Impact**: Pods can't schedule during incidents  
**Fix**: Use `preferred` with high weight

### 5. Volume Expansion Without Planning
**Problem**: Expanding PVC without pod restart  
**Impact**: Filesystem not expanded, app sees old size  
**Fix**: Always restart pod after expansion

## Preventive Measures

### 1. Storage Configuration Validation
```yaml
# Good: Explicit, safe defaults
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  storageClassName: fast-ssd-retain  # Explicit
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
```

### 2. Resource Sizing Best Practices
```yaml
# Good: Adequate resources with room for spikes
resources:
  requests:
    memory: "512Mi"  # 2x minimum
    cpu: "250m"
  limits:
    memory: "1Gi"    # 2x requests
    cpu: "500m"
```

### 3. Probe Configuration
```yaml
# Good: Tolerant of slow startup
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30  # 1.5x typical startup
  periodSeconds: 10
  failureThreshold: 6      # 60s grace period
```

### 4. Anti-Affinity Configuration
```yaml
# Good: Preferred distribution
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: redis
        topologyKey: kubernetes.io/hostname
```

## Monitoring & Alerting

### Critical Metrics
- PVC provisioning latency (alert > 5 minutes)
- Volume attachment success rate (alert < 99.9%)
- Pod restart rate by StatefulSet (alert > 2/hour)
- Storage capacity per namespace (alert > 80%)

### Example Prometheus Alerts
```yaml
- alert: PVCProvisioningSlow
  expr: kube_persistentvolumeclaim_status_phase{phase="Pending"} > 300
  annotations:
    summary: "PVC {{ $labels.persistentvolumeclaim }} pending > 5 minutes"

- alert: StatefulSetPodRestarts
  expr: rate(kube_pod_container_status_restarts_total{pod=~".*-[0-9]+"}[5m]) > 0.033
  annotations:
    summary: "StatefulSet pod {{ $labels.pod }} restarting frequently"
```

## Post-Incident Review

After resolving each issue, document:
1. **Symptom**: What first alerted you?
2. **Detection time**: How long to notice?
3. **Diagnosis time**: How long to find root cause?
4. **Resolution time**: How long to fix?
5. **Root cause**: What actually broke?
6. **Prevention**: How to avoid repeat?

## Practice Scenarios

Use the Break-It-Friday scenarios to practice:
1. Time yourself using The Five-Minute Drill
2. Document your debugging path
3. Identify which minute revealed the issue
4. Create a runbook for similar failures

---

This methodology becomes instinctive with practice. Start with the Five-Minute Drill, expand as needed, and always document your findings.
