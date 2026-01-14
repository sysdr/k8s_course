# Scenario 6: Storage Provisioning Timeout

## Symptom
Cassandra StatefulSet creates first few pods successfully, then provisioning slows dramatically. 
Some PVCs stuck in `Pending` for 10+ minutes.

## What's Broken
Creating 20 × 50Gi volumes simultaneously (1TB total) triggers cloud provider API rate limiting. 
Provisioner can't keep up, causing timeouts and eventual failures.

## Debugging Steps
```bash
# 1. Check PVC provisioning status
kubectl get pvc -n scenario-06
kubectl get pvc -n scenario-06 -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# 2. Check events for rate limiting
kubectl get events -n scenario-06 | grep -i "provision\|timeout\|rate"

# 3. Watch provisioning over time
watch -n 5 'kubectl get pvc -n scenario-06 | grep Pending | wc -l'

# 4. Check StorageClass provisioner logs (if available)
kubectl logs -n kube-system -l app=ebs-csi-controller

# 5. Check cloud provider quotas
# AWS: aws ec2 describe-volumes --query 'length(Volumes)'
# GCP: gcloud compute disks list --format="value(name)" | wc -l
```

## Expected Errors
- PVC: `Waiting for a volume to be created, either by external provisioner or manually`
- Event: `ProvisioningFailed: timeout while waiting for volume to be created`
- Event: `rate limit exceeded` (if cloud provider exposes this)

## The Fix
Stagger StatefulSet rollout:
```yaml
spec:
  replicas: 20
  podManagementPolicy: OrderedReady  # Deploy one at a time
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0  # Start with partition to control rollout speed
```

Or use a deployment controller to add replicas gradually:
```bash
# Scale up slowly
kubectl scale sts cassandra -n scenario-06 --replicas=5
sleep 120
kubectl scale sts cassandra -n scenario-06 --replicas=10
sleep 120
kubectl scale sts cassandra -n scenario-06 --replicas=20
```

## Real-World Context
Datadog hit AWS EBS creation limits when auto-scaling their time-series database. 
300 volumes needed provisioning, but AWS allows max 50/minute. Queue took 6 minutes to clear, 
causing alerts and customer impact.

## Time to Debug
Expert: 15 minutes | Intermediate: 45 minutes | Beginner: 120 minutes
