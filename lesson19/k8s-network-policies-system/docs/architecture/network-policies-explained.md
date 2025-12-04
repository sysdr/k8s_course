# Network Policies Deep Dive

## How Network Policies Work

Network Policies are implemented by Container Network Interface (CNI) plugins:
- **Calico**: Uses iptables or eBPF
- **Cilium**: Uses eBPF exclusively
- **Weave**: Uses iptables

They operate at the Linux kernel level, intercepting packets before they reach pod network interfaces.

## Policy Evaluation

Policies are **additive**. If a pod matches multiple policies:
1. Start with default: Allow all (if no policies) or Deny all (if any policy exists)
2. Union all matching policies
3. Traffic allowed if ANY policy permits it

Example:
```yaml
# Policy 1: Allow from namespace A
- from:
  - namespaceSelector:
      matchLabels:
        name: namespace-a

# Policy 2: Allow from namespace B
- from:
  - namespaceSelector:
      matchLabels:
        name: namespace-b
```

Result: Pod receives traffic from BOTH namespace-a AND namespace-b.

## Common Patterns

### 1. Default Deny-All

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

Creates closed network. Must explicitly allow all traffic.

### 2. Allow DNS

```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        name: kube-system
  ports:
  - protocol: UDP
    port: 53
```

Required for service name resolution.

### 3. Allow Same Namespace

```yaml
ingress:
- from:
  - podSelector: {}
```

Pods in namespace can talk to each other.

### 4. Allow Cross-Namespace

```yaml
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        name: other-namespace
    podSelector:
      matchLabels:
        app: specific-app
```

Only specific app from other namespace can connect.

### 5. Allow External Traffic

```yaml
ingress:
- from:
  - ipBlock:
      cidr: 203.0.113.0/24
  ports:
  - protocol: TCP
    port: 80
```

Allow from specific external IP range.

## Performance Considerations

Network Policies add latency:
- **Calico (iptables)**: <1ms per rule
- **Cilium (eBPF)**: <0.1ms per rule

At 100,000 requests/second:
- 10 rules: negligible impact
- 100 rules: may see 1-5ms additional latency
- 1000+ rules: performance degradation likely

**Best practice**: Keep policies simple. 10-20 rules per namespace is ideal.

## Debugging Checklist

When traffic is blocked:

1. ✅ Check policies exist:
   ```bash
   kubectl get networkpolicies -n <namespace>
   ```

2. ✅ Verify label selectors:
   ```bash
   kubectl get pods --show-labels -n <namespace>
   ```

3. ✅ Check DNS works:
   ```bash
   kubectl exec <pod> -- nslookup <service>
   ```

4. ✅ Test connectivity:
   ```bash
   kubectl exec <pod> -- curl -v <service>
   ```

5. ✅ Review CNI logs:
   ```bash
   kubectl logs -n kube-system -l k8s-app=calico-node
   ```

## Production Patterns

### Automated Policy Generation

Don't write policies manually at scale. Use observed traffic:

1. Deploy services without policies
2. Run traffic for 24-48 hours
3. Observe Istio telemetry
4. Generate policies from observed patterns
5. Apply in "log-only" mode
6. Review logs for false positives
7. Enforce policies

### Policy as Code

Store policies in Git:
- Version control
- Code review
- Automated testing
- GitOps deployment

### Testing Strategy

Create test namespace:
```bash
kubectl create namespace policy-test
kubectl apply -f test-policies/ -n policy-test
```

Run automated tests:
```bash
./test-connectivity.sh policy-test
```

Only promote to production after validation.
