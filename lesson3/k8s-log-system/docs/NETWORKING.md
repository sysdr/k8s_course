# Container Networking Deep Dive

## Service Types and Use Cases

### ClusterIP (Default)
- **Use Case**: Internal service-to-service communication
- **Example**: log-processor service
- **How it works**: Creates a virtual IP in the cluster's service network
- **DNS**: `<service-name>.<namespace>.svc.cluster.local`

### NodePort
- **Use Case**: External access for testing (not production)
- **Example**: Exposing a service on each node's IP
- **Port Range**: 30000-32767
- **Limitation**: Requires knowing node IPs

### LoadBalancer
- **Use Case**: Production external access
- **Example**: Frontend service
- **Cloud Integration**: Creates cloud provider load balancer
- **Cost**: ~$20-30/month per LoadBalancer

### Headless Service (ClusterIP: None)
- **Use Case**: Direct pod-to-pod communication
- **Example**: StatefulSet services (timescaledb-headless)
- **DNS Returns**: Individual pod IPs instead of service VIP
- **Access Pattern**: `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

## Network Flow Example

```
Frontend Pod → Frontend Service (ClusterIP)
    ↓
log-processor Service (ClusterIP) → log-processor Pods (StatefulSet)
    ↓                                          ↓
Redis Service           TimescaleDB Headless Service
    ↓                                          ↓
Redis Pod              timescaledb-0 Pod (specific pod addressing)
```

## DNS Resolution

```bash
# Inside a pod, these all work:
curl http://log-processor:8080              # Short name (same namespace)
curl http://log-processor.log-system:8080   # With namespace
curl http://log-processor.log-system.svc:8080  # With svc
curl http://log-processor.log-system.svc.cluster.local:8080  # FQDN
```

## Network Policy Best Practices

1. **Default Deny**: Start with deny-all, then whitelist
2. **Namespace Isolation**: Separate dev/staging/prod
3. **Least Privilege**: Only allow necessary connections
4. **Egress Control**: Restrict external access
5. **DNS Allow**: Always allow DNS (port 53)

## Service Mesh Benefits

- **mTLS**: Automatic encryption between pods
- **Traffic Management**: Canary deployments, A/B testing
- **Observability**: Automatic metrics and tracing
- **Resilience**: Circuit breakers, retries, timeouts
- **Security**: Fine-grained authorization policies

## Performance Considerations

- **Connection Pooling**: Reuse connections to backend services
- **Keep-Alive**: Enable HTTP keep-alive
- **Service Locality**: Prefer pods on same node (topology hints)
- **Network Plugins**: Choose based on requirements (Calico, Cilium, etc.)
