# Kubernetes Debugging Cheatsheet

## Scheduling Failures

### Pod Stuck in Pending

```bash
# Get the reason
kubectl describe pod <pod> | grep -A 5 "Events:"

# Common messages and fixes:
# - "Insufficient cpu" → Reduce requests or add nodes
# - "Insufficient memory" → Same as above
# - "node(s) didn't match node selector" → Check labels
# - "node(s) had taint" → Add toleration
```

### Check Node Capacity

```bash
# View allocatable vs allocated
kubectl describe node <node> | grep -A 10 "Allocated resources"

# Quick capacity check
kubectl top nodes

# See all requests/limits
kubectl get pods -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[*].resources.requests.cpu,\
MEM_REQ:.spec.containers[*].resources.requests.memory
```

### Node Labels and Taints

```bash
# View all labels
kubectl get nodes --show-labels

# View specific label
kubectl get nodes -l gpu-type=nvidia

# View taints
kubectl describe nodes | grep Taints

# Add/remove taint
kubectl taint nodes <node> key=value:NoSchedule
kubectl taint nodes <node> key=value:NoSchedule-
```

## Networking Failures

### Service Has No Endpoints

```bash
# Check endpoints
kubectl get endpoints <service>

# Compare selectors
kubectl get svc <service> -o jsonpath='{.spec.selector}'
kubectl get pods --show-labels | grep <app-label>

# Quick test
kubectl run test --rm -it --image=busybox -- wget -qO- <service>
```

### DNS Resolution Fails

```bash
# Test from Pod
kubectl exec -it <pod> -- nslookup <service>
kubectl exec -it <pod> -- cat /etc/resolv.conf

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Verify NetworkPolicy allows DNS
kubectl get networkpolicy -o yaml | grep -A 5 "egress"
```

### Connection Refused

```bash
# Check service and endpoints
kubectl get svc,endpoints <service>

# Verify targetPort matches containerPort
kubectl get svc <service> -o yaml | grep -A 5 "ports:"
kubectl get deployment <deploy> -o yaml | grep -A 5 "ports:"

# Test from within cluster
kubectl run test --rm -it --image=busybox -- telnet <service> <port>
```

## Quick Diagnostic Commands

```bash
# All failed Pods
kubectl get pods -A | grep -v Running | grep -v Completed

# Recent warning events
kubectl get events -A --field-selector=type=Warning --sort-by='.lastTimestamp'

# Resource quotas
kubectl describe resourcequota -A

# Network policies
kubectl get networkpolicies -A
```
