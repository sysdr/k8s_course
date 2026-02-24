# Cluster Autoscaler Debug Lab

Production-grade environment for troubleshooting Kubernetes cluster autoscaler issues.

## Quick Start

### Option 1: Local Development (Kind)

```bash
# Create local Kubernetes cluster
cd scripts
./setup-local-cluster.sh

# Deploy cluster autoscaler (for local testing)
kubectl apply -f ../kubernetes/autoscaler/cluster-autoscaler-deployment.yaml
```

### Option 2: AWS EKS Cluster

```bash
# Prerequisites:
# - EKS cluster running
# - kubectl configured for your cluster
# - AWS CLI configured

# Generate IAM policy
cd scripts
./generate-iam-policy.sh my-cluster-name > autoscaler-policy.json

# Create IAM policy and role (AWS Console or CLI)
# Attach role ARN to service account annotation

# Deploy autoscaler
kubectl apply -f ../kubernetes/autoscaler/cluster-autoscaler-deployment.yaml
```

## Debugging Scenarios

### Scenario 1: IAM Permission Failure

Simulates autoscaler with insufficient AWS IAM permissions.

```bash
# Deploy broken autoscaler
kubectl apply -f kubernetes/scenarios/scenario-1-iam-failure.yaml

# Check logs for permission errors
kubectl logs -n kube-system deployment/cluster-autoscaler-broken-iam

# Expected: AccessDeniedException or similar IAM errors
```

**Fix:**
- Update IAM role with correct permissions
- Verify service account annotation
- Check trust relationship in IAM role

### Scenario 2: Node Group Max Size Reached

Cluster hits configured maximum node count.

```bash
# Deploy workload exceeding node capacity
kubectl apply -f kubernetes/scenarios/scenario-2-max-nodes.yaml

# Monitor autoscaler decision
kubectl logs -n kube-system deployment/cluster-autoscaler | grep "max node group size"
```

**Fix:**
- Increase max size in ASG/node group configuration
- Review capacity planning
- Consider multiple node groups

### Scenario 3: Resource Quota Blocking

Namespace quota prevents pod scheduling despite cluster capacity.

```bash
# Create namespace with restrictive quota
kubectl apply -f kubernetes/scenarios/scenario-3-resource-quota.yaml

# Observe quota exhaustion
kubectl describe resourcequota -n quota-limited
```

**Fix:**
- Increase namespace resource quotas
- Remove unnecessary quotas
- Distribute workloads across namespaces

### Scenario 4: Node Selector Mismatch

Pods require node labels that don't exist in any node group.

```bash
# Deploy pods with impossible node selectors
kubectl apply -f kubernetes/scenarios/scenario-4-node-selector.yaml

# Check autoscaler reasoning
kubectl logs -n kube-system deployment/cluster-autoscaler | grep "node group"
```

**Fix:**
- Verify node group labels match pod requirements
- Update node selectors to existing labels
- Create appropriate node groups

### Scenario 5: Taint/Toleration Issues

New nodes have taints that pods don't tolerate.

```bash
# Deploy pods without required tolerations
kubectl apply -f kubernetes/scenarios/scenario-5-taints.yaml

# Observe scheduling failures
kubectl describe pod <pod-name>
```

**Fix:**
- Add tolerations to pod specs
- Remove unnecessary node taints
- Use dedicated node pools for specific workloads

## Debugging Tools

### Comprehensive Debug Script

```bash
cd scripts
./debug-autoscaler.sh
```

This script performs:
1. Autoscaler health check
2. Pending pod analysis
3. Log error scanning
4. IAM configuration verification
5. Node group discovery
6. Resource quota review
7. Scheduling constraint analysis
8. Metrics collection

### Trigger Scaling Test

```bash
# Create deployment requiring 30 nodes worth of resources
./trigger-scaling.sh 30 2000m 4Gi

# Monitor autoscaler behavior
kubectl logs -n kube-system deployment/cluster-autoscaler -f
```

### Setup Monitoring

```bash
# Install Prometheus and Grafana
./setup-monitoring.sh

# Access dashboards
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Visit http://localhost:3000 (admin/admin)
```

## Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `cluster_autoscaler_failed_scale_ups_total` | Failed scale-up attempts | >3 in 15min |
| `cluster_autoscaler_unschedulable_pods_count` | Pods waiting for nodes | >5 for 10min |
| `cluster_autoscaler_nodes_count` | Current node count | Near max limit |
| `cluster_autoscaler_errors_total` | Autoscaler errors | >0.1/sec |

## Common Issues and Solutions

### Issue: Autoscaler logs show "AccessDenied"

**Root Cause:** IAM role lacks required permissions

**Solution:**
```bash
# Generate correct policy
./generate-iam-policy.sh > policy.json

# Update IAM role
aws iam put-role-policy --role-name <role> --policy-name AutoscalerPolicy --policy-document file://policy.json
```

### Issue: Pods pending but autoscaler doing nothing

**Root Causes:**
1. Max nodes reached
2. Node selector mismatch
3. Resource quota exhausted
4. Insufficient IAM permissions

**Debugging:**
```bash
# Run comprehensive debug
./debug-autoscaler.sh

# Check specific pod
kubectl describe pod <pod-name>

# Review autoscaler decision log
kubectl logs -n kube-system deployment/cluster-autoscaler | grep -i "scale"
```

### Issue: Nodes added but pods still pending

**Root Causes:**
1. Taints without tolerations
2. Node not becoming Ready
3. Pod affinity/anti-affinity rules

**Solution:**
```bash
# Check node status
kubectl get nodes

# Check node conditions
kubectl describe node <node-name>

# Verify pod tolerations
kubectl get pod <pod-name> -o yaml | grep -A 10 tolerations
```

## Production Checklist

- [ ] IAM role has minimum required permissions
- [ ] Node group max size allows for traffic spikes (3x average)
- [ ] Resource quotas set appropriately or removed
- [ ] Pod resource requests accurately reflect usage
- [ ] Node selectors match available node group labels
- [ ] Tolerations configured for tainted nodes
- [ ] Monitoring and alerting configured
- [ ] Scale-down delay set to prevent churn (10m+)
- [ ] PodDisruptionBudgets configured for critical apps
- [ ] Autoscaler version matches Kubernetes version

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes API                        │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │ Watch pending pods
                           │
┌─────────────────────────────────────────────────────────┐
│              Cluster Autoscaler Pod                      │
│  ┌────────────────────────────────────────────────┐    │
│  │  Control Loop:                                  │    │
│  │  1. Watch for pending pods                      │    │
│  │  2. Calculate required nodes                    │    │
│  │  3. Call cloud provider API                     │    │
│  │  4. Wait for nodes to join                      │    │
│  │  5. Verify scheduling                           │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           │ SetDesiredCapacity
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Cloud Provider (AWS/GCP/Azure)              │
│  ┌────────────────────────────────────────────────┐    │
│  │  Auto Scaling Group / Managed Instance Group   │    │
│  │  - Min: 3 nodes                                 │    │
│  │  - Max: 100 nodes                               │    │
│  │  - Desired: X (calculated by autoscaler)        │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Cleanup

```bash
cd scripts
./cleanup.sh

# Remove local kind cluster (if used)
kind delete cluster --name autoscaler-debug
```

## Additional Resources

- [Cluster Autoscaler Documentation](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [AWS IAM Permissions Guide](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md)
- [Autoscaler FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)

## Next Steps

After mastering cluster autoscaler debugging:
1. Explore Karpenter for faster, more efficient autoscaling
2. Implement multi-cluster autoscaling patterns
3. Build custom metrics-based autoscaling with KEDA
4. Design multi-region capacity management
