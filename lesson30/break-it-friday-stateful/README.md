# Break-It-Friday: Stateful Application Debugging System

A production-grade Kubernetes debugging environment featuring six intentionally broken scenarios that represent real-world stateful application failures. Practice systematic troubleshooting methodologies used by Netflix, Datadog, and Stripe.

## 🎯 Learning Objectives

By completing this lesson, you will:
- Master systematic debugging of PersistentVolumeClaim failures
- Diagnose and resolve StatefulSet deployment issues
- Fix database crashloops and startup problems
- Resolve volume permission and security context conflicts
- Understand pod affinity/anti-affinity scheduling constraints
- Handle storage provisioning timeouts and rate limiting

## 🏗️ System Architecture

```
Break-It-Friday Debugging System
├── 6 Broken Scenarios (Intentional Failures)
│   ├── Scenario 1: PVC Pending - StorageClass Mismatch
│   ├── Scenario 2: Resource Quota Exhaustion
│   ├── Scenario 3: PostgreSQL CrashLoopBackOff
│   ├── Scenario 4: Volume Mount Permission Denied
│   ├── Scenario 5: Redis Anti-Affinity Too Restrictive
│   └── Scenario 6: Storage Provisioning Timeout
├── Database API Service (Health Monitoring)
├── Storage Monitor Service (PVC/PV Tracking)
└── React Dashboard (Real-time Status)
```

## 📋 Prerequisites

- Docker installed
- kind or minikube installed
- kubectl installed
- 8GB RAM minimum (16GB recommended)
- Basic Kubernetes knowledge

## 🚀 Quick Start

### 1. Generate the System
```bash
# This script is already generated
cd break-it-friday-stateful
```

### 2. Setup Local Cluster
```bash
cd scripts
./setup-cluster.sh
```

This creates:
- 3-node kind cluster
- Scenario namespaces (scenario-01 through scenario-06)
- StorageClass 'fast-ssd-retain'

### 3. Deploy Broken Scenarios
```bash
./deploy-scenarios.sh
```

### 4. Check Initial Status
```bash
./check-status.sh
```

You should see multiple failures:
- PVCs stuck in Pending
- Pods in CrashLoopBackOff
- Scheduling failures

### 5. Start Debugging!

Each scenario has a README with:
- Symptom description
- Debugging steps
- Expected errors
- Real-world context
- Solution hints

## 🔧 Debugging Scenarios

### Scenario 1: PVC Pending (Easy)
**Symptom**: PostgreSQL StatefulSet pod stuck in Pending  
**Root Cause**: StorageClass name typo  
**Location**: `scenarios/01-pvc-pending/`  
**Time**: 2-30 minutes  

```bash
kubectl get pvc -n scenario-01
kubectl describe pvc postgres-data-postgres-0 -n scenario-01
kubectl get storageclass
```

### Scenario 2: Resource Quota (Easy)
**Symptom**: MySQL StatefulSet stops at 2/3 replicas  
**Root Cause**: Quota too restrictive  
**Location**: `scenarios/02-resource-quota/`  
**Time**: 3-45 minutes  

```bash
kubectl get resourcequota -n scenario-02
kubectl describe quota storage-quota -n scenario-02
```

### Scenario 3: PostgreSQL CrashLoop (Medium)
**Symptom**: Pod repeatedly restarts, OOMKilled  
**Root Cause**: Memory limits too low, probe timing wrong  
**Location**: `scenarios/03-postgres-crashloop/`  
**Time**: 5-60 minutes  

```bash
kubectl logs postgres-0 -n scenario-03 --previous
kubectl describe pod postgres-0 -n scenario-03
```

### Scenario 4: Volume Permissions (Medium)
**Symptom**: MongoDB running but can't write to volume  
**Root Cause**: SecurityContext UID mismatch  
**Location**: `scenarios/04-volume-permissions/`  
**Time**: 10-90 minutes  

```bash
kubectl exec mongodb-0 -n scenario-04 -- ls -la /data/db
kubectl exec mongodb-0 -n scenario-04 -- id
```

### Scenario 5: Redis Anti-Affinity (Medium)
**Symptom**: Only 3 of 5 Redis pods schedule  
**Root Cause**: Required anti-affinity too strict for 3-node cluster  
**Location**: `scenarios/05-redis-antiaffinity/`  
**Time**: 5-60 minutes  

```bash
kubectl describe pod redis-3 -n scenario-05
kubectl get nodes
```

### Scenario 6: Storage Timeout (Hard)
**Symptom**: Cassandra PVCs provision slowly, some timeout  
**Root Cause**: Cloud provider rate limiting on bulk volume creation  
**Location**: `scenarios/06-storage-timeout/`  
**Time**: 15-120 minutes  

```bash
watch -n 5 'kubectl get pvc -n scenario-06 | grep Pending | wc -l'
kubectl get events -n scenario-06 | grep -i provision
```

## 🔍 Systematic Debugging Process

### The Five-Minute Drill (Datadog's Methodology)

**Minute 1: Verify Storage Stack**
```bash
kubectl get pvc -n <namespace>
kubectl describe pvc <pvc-name> -n <namespace>
kubectl get storageclass
```

**Minute 2: Inspect Volume Binding**
```bash
kubectl get pv
kubectl describe pv <pv-name>
kubectl get resourcequota -A
```

**Minute 3: Validate Pod-Volume Attachment**
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.volumes}'
```

**Minute 4: Examine StatefulSet Ordering**
```bash
kubectl get statefulset -n <namespace>
kubectl describe sts <name> -n <namespace>
```

**Minute 5: Analyze Application State**
```bash
kubectl logs <pod-name> -n <namespace> --tail=100
kubectl exec <pod-name> -n <namespace> -- df -h
```

## 📊 Solutions

Located in `solutions/` directory:
- `01-pvc-pending-FIXED.yaml`
- `02-resource-quota-FIXED.yaml`
- `03-postgres-crashloop-FIXED.yaml`
- `04-volume-permissions-FIXED.yaml`
- `05-redis-antiaffinity-FIXED.yaml`
- `06-storage-timeout-FIXED.yaml`

**Don't look until you've tried debugging first!**

## 🎓 Production Debugging Tips

### PVC Stuck in Pending
1. Check StorageClass exists and matches name exactly
2. Verify default StorageClass if none specified
3. Check resource quotas aren't exceeded
4. Confirm node capacity and attachment limits
5. Review cloud provider quotas

### CrashLoopBackOff
1. Check previous pod logs: `kubectl logs <pod> --previous`
2. Look for OOMKilled in pod description
3. Verify resource limits are adequate for startup
4. Check probe timing (initialDelay vs actual startup time)
5. Review application logs for startup errors

### Volume Permission Issues
1. Check pod security context (runAsUser, fsGroup)
2. Verify container image default user
3. Exec into pod and check file ownership
4. Compare expected UID/GID with actual
5. Test with permissive security context first

### Scheduling Failures
1. Describe pending pod to see reason
2. Check node selector and affinity rules
3. Verify node capacity and taints
4. Review resource requests vs available capacity
5. Check PodDisruptionBudgets

## 📈 Monitoring & Observability

### Check Overall Status
```bash
./scripts/check-status.sh
```

### Watch Real-time Changes
```bash
watch -n 2 'kubectl get pods -A'
watch -n 2 'kubectl get pvc -A'
```

### Stream Events
```bash
kubectl get events -A --watch
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Storage Metrics
```bash
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

## 🧹 Cleanup

### Remove All Scenarios
```bash
./scripts/cleanup.sh
```

### Delete Entire Cluster
```bash
kind delete cluster --name break-it-friday
```

## 🔥 Real-World Context

### Scenario 1 Context
**Company**: Major e-commerce platform  
**Impact**: $2.7M lost during Black Friday  
**Cause**: StorageClass typo in Terraform  
**Lesson**: Always validate StorageClass names in CI/CD

### Scenario 2 Context
**Company**: Capital One  
**Impact**: Database split-brain, data inconsistency  
**Cause**: Quota prevented new replicas during scaling  
**Lesson**: Monitor quota usage, alert at 80%

### Scenario 3 Context
**Company**: Airbnb  
**Impact**: 2-hour payment system outage  
**Cause**: "Optimized" memory limits broke initialization  
**Lesson**: Test resource limits under load before deploying

### Scenario 4 Context
**Company**: Stripe  
**Impact**: 3-hour analytics pipeline downtime  
**Cause**: MongoDB image upgrade changed default UID  
**Lesson**: Validate security contexts during image updates

### Scenario 5 Context
**Company**: Netflix  
**Impact**: Cascading cache failures during incident  
**Cause**: Anti-affinity prevented pod rescheduling  
**Lesson**: Use preferred anti-affinity for critical services

### Scenario 6 Context
**Company**: Datadog  
**Impact**: 6-minute delay in time-series database scaling  
**Cause**: AWS EBS rate limiting (50 volumes/minute)  
**Lesson**: Stagger large-scale provisioning operations

## 📚 Additional Resources

- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)
- [StatefulSet Concepts](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

## 🎯 Success Criteria

You've mastered this lesson when you can:
- [ ] Fix all 6 scenarios independently
- [ ] Explain the root cause of each failure
- [ ] Apply The Five-Minute Drill systematically
- [ ] Identify similar issues in production logs
- [ ] Propose preventive measures for each failure type
- [ ] Estimate time-to-resolution for each scenario class

## 💡 Next Steps

After completing Break-It-Friday:
1. Practice on your own broken scenarios
2. Apply debugging skills to production incidents
3. Build automated tests to prevent these failures
4. Share post-mortems with your team
5. Create runbooks based on lessons learned

---

**Remember**: Most production stateful failures follow patterns. The debugging skills you build today become the automation that prevents tomorrow's incidents.

Good luck, and happy debugging! 🐛🔍
