# Cluster Autoscaler Debugging Flowchart

## Decision Tree for Autoscaler Issues

```
Is the autoscaler pod running?
├─ No → Check deployment/logs: kubectl get deployment cluster-autoscaler -n kube-system
└─ Yes ↓

Are there pending pods?
├─ No → No scaling needed, autoscaler working correctly
└─ Yes ↓

Do pending pods have "Unschedulable" status?
├─ No → Issue with pod spec, not autoscaler
└─ Yes ↓

Check autoscaler logs for scale-up attempts
├─ "max node group size reached" → Increase ASG max size
├─ "AccessDenied" → Fix IAM permissions
├─ "node group doesn't exist" → Tag ASG correctly
├─ "no expansion candidates" → Check node selectors
└─ No scale-up attempt logged ↓

Are node selectors/affinity rules satisfiable?
├─ No → Fix pod selectors to match available node groups
└─ Yes ↓

Are resource quotas blocking scheduling?
├─ Yes → Increase quota or remove
└─ No ↓

Do new nodes have taints?
├─ Yes → Add tolerations to pod spec
└─ No ↓

Is cloud provider API healthy?
├─ No → Check cloud provider status, instance availability
└─ Yes ↓

Are nodes joining the cluster?
├─ No → Check VPC/networking, kubelet config
└─ Yes ↓

Are nodes becoming Ready?
├─ No → Check node conditions, CNI plugin
└─ Yes ↓

Are pods scheduling to new nodes?
├─ No → Check remaining scheduling constraints
└─ Yes → Autoscaling working correctly!
```

## Log Analysis Patterns

### Successful Scale-Up
```
Upcoming 1 nodes
Final scale-up plan: [{nodegroup-name 3->4 (max: 10)}]
Scale-up: setting group nodegroup-name size to 4
```

### IAM Permission Failure
```
Failed to increase node group size: AccessDeniedException
Could not find any suitable instance types
```

### Max Nodes Reached
```
max node group size reached
Skipping node group - at max size
```

### Node Selector Mismatch
```
no node group can satisfy requirements
0/N nodes match node selector
```
