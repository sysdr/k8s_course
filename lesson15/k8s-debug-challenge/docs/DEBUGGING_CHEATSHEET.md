# Kubernetes Debugging Cheatsheet

## Quick Reference for Common Debugging Commands

### Pod Investigation

```bash
# List all pods with details
kubectl get pods -n <namespace> -o wide --show-labels

# Describe a specific pod
kubectl describe pod <pod-name> -n <namespace>

# Get pod logs
kubectl logs <pod-name> -n <namespace>

# Get logs from previous crash
kubectl logs <pod-name> -n <namespace> --previous

# Get logs from all containers in a pod
kubectl logs <pod-name> -n <namespace> --all-containers

# Follow logs in real-time
kubectl logs -f <pod-name> -n <namespace>

# Get logs from a specific container in a multi-container pod
kubectl logs <pod-name> -c <container-name> -n <namespace>
```

### Service & Networking

```bash
# List all services
kubectl get svc -n <namespace>

# Describe a service
kubectl describe svc <service-name> -n <namespace>

# Get service endpoints
kubectl get endpoints <service-name> -n <namespace>

# Check service selector and labels
kubectl get svc <service-name> -n <namespace> -o yaml | grep -A 5 selector
kubectl get pods -n <namespace> --show-labels

# Test DNS from within a pod
kubectl exec -it <pod-name> -n <namespace> -- nslookup <service-name>

# Test connectivity from within a pod
kubectl exec -it <pod-name> -n <namespace> -- curl http://<service-name>:<port>/path
```

### Events & Troubleshooting

```bash
# Get all events sorted by timestamp
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Get events for a specific pod
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>

# Watch events in real-time
kubectl get events -n <namespace> --watch
```

### Interactive Debugging

```bash
# Execute a shell in a running pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# Run a one-off command
kubectl exec <pod-name> -n <namespace> -- <command>

# Copy files from pod to local
kubectl cp <namespace>/<pod-name>:/path/to/file ./local-file

# Copy files from local to pod
kubectl cp ./local-file <namespace>/<pod-name>:/path/to/file
```

### Resource Status

```bash
# Get all resources in namespace
kubectl get all -n <namespace>

# Check deployments
kubectl get deployments -n <namespace>
kubectl describe deployment <deployment-name> -n <namespace>

# Check replica sets
kubectl get rs -n <namespace>

# Check persistent volumes
kubectl get pv
kubectl get pvc -n <namespace>

# Check network policies
kubectl get networkpolicies -n <namespace>
kubectl describe networkpolicy <policy-name> -n <namespace>
```

### Common Debugging Patterns

#### Pattern 1: Pod Crash Investigation
```bash
# 1. Check pod status
kubectl get pod <pod-name> -n <namespace>

# 2. Get recent events
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Events

# 3. Check current logs
kubectl logs <pod-name> -n <namespace> --tail=50

# 4. Check previous crash logs
kubectl logs <pod-name> -n <namespace> --previous
```

#### Pattern 2: Service Connection Issues
```bash
# 1. Verify service exists
kubectl get svc -n <namespace>

# 2. Check endpoints
kubectl get endpoints <service-name> -n <namespace>

# 3. Verify selectors match
kubectl get svc <service-name> -n <namespace> -o jsonpath='{.spec.selector}'
kubectl get pods -n <namespace> -l app=<label>

# 4. Test DNS
kubectl run test-pod --image=busybox -n <namespace> -- sleep 3600
kubectl exec test-pod -n <namespace> -- nslookup <service-name>
```

#### Pattern 3: Network Policy Debugging
```bash
# 1. List network policies
kubectl get networkpolicies -n <namespace>

# 2. Describe policy details
kubectl describe networkpolicy <policy-name> -n <namespace>

# 3. Check pod labels
kubectl get pods -n <namespace> --show-labels

# 4. Test connectivity
kubectl exec <pod-name> -n <namespace> -- curl -v http://<service>:<port>
```

### Output Formatting

```bash
# JSON output
kubectl get pod <pod-name> -n <namespace> -o json

# YAML output
kubectl get pod <pod-name> -n <namespace> -o yaml

# JSONPath queries
kubectl get pods -n <namespace> -o jsonpath='{.items[*].status.podIP}'
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Custom columns
kubectl get pods -n <namespace> -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP
```

### Port Forwarding for Local Testing

```bash
# Forward pod port to local
kubectl port-forward <pod-name> <local-port>:<pod-port> -n <namespace>

# Forward service port to local
kubectl port-forward svc/<service-name> <local-port>:<service-port> -n <namespace>

# Forward in background
kubectl port-forward <pod-name> <local-port>:<pod-port> -n <namespace> &
```

### Debugging Specific Scenarios

#### CrashLoopBackOff
```bash
# Check restart count
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].restartCount}'

# Check exit code
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'

# Check restart reason
kubectl describe pod <pod-name> -n <namespace> | grep "Last State"
```

#### ImagePullBackOff
```bash
# Check image name and tag
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'

# Check pull policy
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].imagePullPolicy}'

# Check events for pull errors
kubectl describe pod <pod-name> -n <namespace> | grep "Failed to pull image"
```

#### Pending Pods
```bash
# Check scheduling events
kubectl describe pod <pod-name> -n <namespace> | grep "FailedScheduling"

# Check node resources
kubectl top nodes

# Check node conditions
kubectl describe nodes | grep -A 5 "Conditions"
```

### Clean Up

```bash
# Delete pod (will be recreated by deployment)
kubectl delete pod <pod-name> -n <namespace>

# Force delete stuck pod
kubectl delete pod <pod-name> -n <namespace> --force --grace-period=0

# Delete all pods with label
kubectl delete pods -l app=<label> -n <namespace>

# Delete namespace (and everything in it)
kubectl delete namespace <namespace>
```

### Useful Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kl='kubectl logs'
alias klf='kubectl logs -f'
alias kex='kubectl exec -it'
alias kctx='kubectl config use-context'
```

### Pro Tips

1. **Use `-o wide` for more details**: Always add `-o wide` when listing resources
2. **Check events first**: Events often tell you exactly what's wrong
3. **Use `--previous` for crash logs**: Don't forget to check the previous container logs
4. **Label everything**: Consistent labeling makes debugging much easier
5. **Test connectivity from within**: Use `kubectl exec` to test from inside the cluster
6. **Watch in real-time**: Use `-w` or `--watch` to see changes as they happen
7. **Use port-forward for quick access**: Great for testing without exposing services
8. **Check resource limits**: OOMKilled often means insufficient memory limits

### Emergency Quick Fixes

```bash
# Restart deployment
kubectl rollout restart deployment <deployment-name> -n <namespace>

# Scale to zero and back
kubectl scale deployment <deployment-name> --replicas=0 -n <namespace>
kubectl scale deployment <deployment-name> --replicas=3 -n <namespace>

# Edit live resource
kubectl edit deployment <deployment-name> -n <namespace>

# Patch specific field
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"replicas":3}}'
```
