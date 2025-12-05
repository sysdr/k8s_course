# Kubernetes Networking Debugging Cheatsheet

## The Five-Minute Drill

### 1. Check Resource Existence

```bash
kubectl get pods -n <namespace>
kubectl get svc -n <namespace>
kubectl get ingress -n <namespace>
kubectl get networkpolicies -n <namespace>
```

### 2. Check Pod Health

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # Previous container logs
```

### 3. Check Service → Pod Connection

```bash
# Check if service has endpoints
kubectl get endpoints <service-name> -n <namespace>

# Compare service selector with pod labels
kubectl get svc <service-name> -n <namespace> -o yaml | grep -A5 selector
kubectl get pods -n <namespace> --show-labels
```

### 4. Check Ingress Configuration

```bash
kubectl describe ingress <ingress-name> -n <namespace>

# Verify backend service names and ports match actual services
kubectl get svc -n <namespace>
```

### 5. Test Internal Connectivity

```bash
# Run a debug pod
kubectl run debug --rm -it --image=nicolaka/netshoot -n <namespace> -- bash

# Inside the pod:
curl http://<service-name>:<port>/health
nslookup <service-name>
traceroute <service-name>
```

### 6. Check NetworkPolicies

```bash
# List all policies
kubectl get networkpolicies -n <namespace>

# Check specific policy
kubectl describe networkpolicy <policy-name> -n <namespace>

# Temporarily disable to test (NOT FOR PRODUCTION)
kubectl delete networkpolicy --all -n <namespace>
```

### 7. Debug Istio Issues

```bash
# Analyze Istio configuration
istioctl analyze -n <namespace>

# Check proxy configuration
istioctl proxy-config routes <pod-name> -n <namespace>
istioctl proxy-config clusters <pod-name> -n <namespace>

# Check VirtualService and DestinationRule
kubectl get virtualservices -n <namespace>
kubectl get destinationrules -n <namespace>
```

## Common Issues and Solutions

### Issue: 404 from Ingress

**Symptoms**: External requests return 404

**Debug Steps**:
1. Check Ingress exists: `kubectl get ingress -n <ns>`
2. Check backend service name: `kubectl describe ingress <name> -n <ns>`
3. Verify service exists: `kubectl get svc <backend-service> -n <ns>`
4. Check service has endpoints: `kubectl get endpoints <backend-service> -n <ns>`

**Common Causes**:
- Typo in service name in Ingress rule
- Service port mismatch
- Path mismatch

### Issue: Service Has No Endpoints

**Symptoms**: `kubectl get endpoints` shows `<none>`

**Debug Steps**:
1. Check service selector: `kubectl get svc <name> -n <ns> -o yaml | grep -A3 selector`
2. Check pod labels: `kubectl get pods -n <ns> --show-labels`
3. Verify labels match exactly

**Common Causes**:
- Label selector mismatch
- Typo in label key or value
- Missing label on pods

### Issue: Pod Can't Reach Another Service

**Symptoms**: Connection refused, timeout errors

**Debug Steps**:
1. Check NetworkPolicies: `kubectl get networkpolicies -n <ns>`
2. Verify DNS resolution: `kubectl exec -it <pod> -n <ns> -- nslookup <service>`
3. Test connectivity: `kubectl exec -it <pod> -n <ns> -- curl http://<service>:<port>`

**Common Causes**:
- NetworkPolicy blocking traffic
- DNS resolution failure
- Service name typo in application code

### Issue: Istio Traffic Routing Failure

**Symptoms**: 503 errors, "no healthy upstream" errors

**Debug Steps**:
1. Run Istio analysis: `istioctl analyze -n <ns>`
2. Check VirtualService: `kubectl describe vs <name> -n <ns>`
3. Check DestinationRule: `kubectl describe dr <name> -n <ns>`
4. Verify subset labels match pod labels

**Common Causes**:
- VirtualService referencing non-existent subset
- DestinationRule missing subset definition
- Subset labels don't match pod labels

## Production Debugging Principles

1. **Never Guess**: Follow the systematic checklist
2. **Trust Nothing**: Verify every assumption
3. **Work Layer by Layer**: Start at Ingress, work inward
4. **Check Endpoints First**: Most issues are here
5. **Read Events**: `kubectl describe` events tell the story
6. **Test from Inside**: Use debug pods to eliminate variables
7. **Document as You Go**: Take notes for post-mortem

## Essential Tools

- `kubectl`: Core Kubernetes CLI
- `curl`: Test HTTP endpoints
- `nslookup`/`dig`: DNS debugging
- `netshoot`: Swiss-army knife debug container
- `istioctl`: Istio debugging and analysis
- `tcpdump`: Network packet analysis (advanced)

## Quick Reference: One-Liners

```bash
# Check all pods are running
kubectl get pods -n <ns> | grep -v Running

# Get pod logs for all containers
kubectl logs -n <ns> <pod-name> --all-containers=true

# Describe all failing pods
kubectl get pods -n <ns> --field-selector=status.phase!=Running,status.phase!=Succeeded | \
  tail -n +2 | awk '{print $1}' | xargs -I {} kubectl describe pod {} -n <ns>

# Check which services have no endpoints
for svc in $(kubectl get svc -n <ns> -o name); do \
  name=$(echo $svc | cut -d'/' -f2); \
  endpoints=$(kubectl get endpoints $name -n <ns> -o jsonpath='{.subsets[*].addresses[*].ip}'); \
  [ -z "$endpoints" ] && echo "No endpoints: $name"; \
done

# Test all service health endpoints
for svc in $(kubectl get svc -n <ns> -o name); do \
  name=$(echo $svc | cut -d'/' -f2); \
  kubectl run test-$name --rm -it --image=curlimages/curl -n <ns> -- curl -m 5 http://$name/health; \
done
```

---

Remember: The best debuggers aren't the fastest—they're the most systematic.
