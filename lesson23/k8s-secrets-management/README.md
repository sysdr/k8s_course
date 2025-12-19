# Kubernetes Secrets Management Platform

Production-grade secrets management platform demonstrating enterprise patterns used by Datadog, Splunk, and major cloud providers.

## Architecture Overview

This system implements five layers of secrets security:

1. **Kubernetes Native Secrets** - Base64-encoded, etcd-stored credentials
2. **External Secrets Operator** - Simulated Vault integration for centralized management
3. **Secret Volume Mounts** - Hot-reload secrets without pod restarts
4. **mTLS Encryption** - Istio service mesh for encrypted pod-to-pod communication
5. **Audit and Compliance** - Complete secrets access logging

## System Components

### Core Services

- **Vault Simulator** - Educational HashiCorp Vault implementation
  - PostgreSQL-backed secret store
  - Automatic rotation every 5 minutes
  - Audit logging for all operations
  - Token-based authentication

- **Log Ingestion Service** - Receives logs with API key authentication
  - Hot-reloads API keys from volume mounts
  - Supports batch and single log ingestion
  - Prometheus metrics for observability

- **Log Processing Service** - Processes and stores logs
  - Database credential hot-reload
  - Connection pool rotation on password change
  - Zero-downtime credential updates

- **Analytics API Service** - Multi-secret analytics queries
  - Database, external API, and OAuth credentials
  - Demonstrates multiple secret types
  - Integration with external services

- **Secrets Rotation Service** - Orchestrates automatic rotation
  - Configurable rotation intervals
  - Grace period handling
  - Manual rotation triggers

### Frontend

- React dashboard showing:
  - Service health with secrets status
  - Real-time rotation status
  - Audit log visualization
  - Security metrics

## Prerequisites

- Docker Desktop or Docker Engine
- kind (Kubernetes in Docker)
- kubectl
- 8GB RAM minimum
- 20GB disk space

## Quick Start

### 1. Setup Kubernetes Cluster

```bash
cd k8s-secrets-management
./scripts/setup-cluster.sh
```

This creates a 3-node kind cluster with:
- 1 control plane node
- 2 worker nodes
- Istio service mesh installed
- Ingress controller configured

### 2. Build Container Images

```bash
./scripts/build.sh
```

Builds and loads all service images:
- vault-simulator:latest
- log-ingestion-service:latest
- log-processing-service:latest
- analytics-api-service:latest
- secrets-rotation-service:latest
- frontend:latest

### 3. Deploy Platform

```bash
./scripts/deploy.sh
```

Deploys in order:
1. Namespace creation
2. PostgreSQL StatefulSet
3. Vault Simulator
4. Microservices with secrets
5. Frontend
6. Monitoring stack (Prometheus + Grafana)
7. Istio configuration

### 4. Verify Deployment

```bash
kubectl get pods -n secrets-platform
```

Expected output:
```
NAME                                       READY   STATUS    RESTARTS   AGE
postgres-0                                 1/1     Running   0          2m
vault-simulator-xxxx                       1/1     Running   0          1m
log-ingestion-service-xxxx                 1/1     Running   0          1m
log-processing-service-xxxx                1/1     Running   0          1m
analytics-api-service-xxxx                 1/1     Running   0          1m
secrets-rotation-service-xxxx              1/1     Running   0          1m
frontend-xxxx                              1/1     Running   0          1m
prometheus-xxxx                            1/1     Running   0          1m
grafana-xxxx                               1/1     Running   0          1m
```

## Accessing Services

### Frontend Dashboard
```bash
# Via LoadBalancer (if available)
http://localhost

# Via port-forward
kubectl port-forward -n secrets-platform svc/frontend 8080:80
# Then open http://localhost:8080
```

### Grafana
```bash
kubectl port-forward -n secrets-platform svc/grafana 3000:3000
# Open http://localhost:3000
# Default credentials: admin / admin
```

### Prometheus
```bash
kubectl port-forward -n secrets-platform svc/prometheus 9090:9090
# Open http://localhost:9090
```

### Vault Simulator
```bash
kubectl port-forward -n secrets-platform svc/vault-simulator 8080:8080
# API available at http://localhost:8080
```

## Testing Secrets Management

### Test Secret Mounting
```bash
./scripts/test-secrets.sh
```

### Manual Secret Rotation
```bash
# Get vault token
VAULT_TOKEN=$(kubectl exec -n secrets-platform deployment/secrets-rotation-service -- \
    curl -s http://vault-simulator:8080/v1/auth/token/create | jq -r '.auth.client_token')

# Trigger rotation
kubectl exec -n secrets-platform deployment/secrets-rotation-service -- \
    curl -X POST http://localhost:8080/api/v1/rotation/trigger/ingestion-api-keys
```

### View Audit Logs
```bash
kubectl exec -n secrets-platform deployment/vault-simulator -- \
    curl -s -H "X-Vault-Token: demo-token" \
    http://localhost:8080/v1/sys/audit | jq .
```

### Check Secret Hot-Reload
```bash
# Update a secret
kubectl edit secret ingestion-api-keys -n secrets-platform

# Watch pod logs for reload detection
kubectl logs -n secrets-platform deployment/log-ingestion-service -f
```

## Production Patterns Demonstrated

### 1. Zero-Downtime Rotation

Services check for updated secrets every 30 seconds without restart:

```python
async def reload_api_keys():
    """Hot-reload API keys from volume mount"""
    if os.path.exists(SECRETS_FILE):
        stat = os.stat(SECRETS_FILE)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        if last_reload_time is None or mtime > last_reload_time:
            # Reload secrets
            async with aiofiles.open(SECRETS_FILE, 'r') as f:
                content = await f.read()
                # Update in-memory secrets
```

### 2. Connection Pool Rotation

Database services reconnect pools on password change:

```python
async def reconnect_database():
    """Reconnect database pool with new credentials"""
    if db_pool:
        await db_pool.close()
    
    db_pool = await asyncpg.create_pool(
        password=new_password  # Updated credential
    )
```

### 3. Least Privilege Access

Each service has its own ServiceAccount with minimal permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: log-ingestion-sa
---
# Only this service can read ingestion API keys
```

### 4. Audit Trail

Every secret access logged to Vault audit backend:

```python
await conn.execute(
    "INSERT INTO audit_log (operation, path, token_hash) VALUES ($1, $2, $3)",
    "read", path, hash_token(token)
)
```

### 5. Failure Resilience

Services continue with cached secrets if Vault unavailable:

```python
# 5-minute TTL on cached secrets
# Alerts if secrets become stale
```

## Troubleshooting

### Secrets Not Loading

```bash
# Check secret exists
kubectl get secret ingestion-api-keys -n secrets-platform

# Check volume mount
kubectl describe pod -n secrets-platform -l app=log-ingestion-service

# Check file permissions
kubectl exec -n secrets-platform deployment/log-ingestion-service -- \
    ls -la /var/run/secrets/api-keys/
```

### Rotation Not Working

```bash
# Check rotation service logs
kubectl logs -n secrets-platform deployment/secrets-rotation-service

# Verify Vault connectivity
kubectl exec -n secrets-platform deployment/secrets-rotation-service -- \
    curl -s http://vault-simulator:8080/health
```

### Database Connection Failures

```bash
# Check PostgreSQL is running
kubectl get pods -n secrets-platform -l app=postgres

# Verify database credentials
kubectl get secret database-credentials -n secrets-platform -o jsonpath='{.data.credentials}' | base64 -d | jq .

# Test connection from service
kubectl exec -n secrets-platform deployment/log-processing-service -- \
    curl -s http://localhost:8080/health
```

### Service Not Ready

```bash
# Check readiness probe
kubectl describe pod -n secrets-platform <pod-name>

# View service logs
kubectl logs -n secrets-platform <pod-name>

# Check secret mounts
kubectl exec -n secrets-platform <pod-name> -- ls -la /var/run/secrets/
```

## Security Best Practices Implemented

1. **Encryption at Rest** - All secrets base64-encoded in etcd
2. **Encryption in Transit** - Istio mTLS for pod-to-pod communication
3. **Least Privilege** - Service-specific RBAC permissions
4. **Immutable Secrets** - Volume mounts read-only (0400 permissions)
5. **Audit Logging** - All secret access tracked
6. **Automatic Rotation** - 5-minute rotation in demo (30-day production)
7. **Grace Periods** - Old credentials valid during rotation
8. **No Root** - All containers run as non-root users
9. **Resource Limits** - CPU/memory quotas enforced
10. **Network Policies** - Pod-to-pod communication restricted

## Scaling Considerations

### High Availability

- Vault Simulator: 2 replicas with PostgreSQL backend
- Log Ingestion: HPA scales 3-10 replicas based on CPU
- All services: PodDisruptionBudgets ensure availability

### Performance

- Connection pooling for database access
- Prometheus metrics for bottleneck identification
- Istio circuit breakers for fault tolerance

### Cost Optimization

- Right-sized resource requests/limits
- HPA prevents over-provisioning
- StatefulSet for PostgreSQL minimizes cloud storage costs

## Next Steps

1. **Add External Secrets Operator** - Real Vault/AWS Secrets Manager integration
2. **Implement SOPS** - Encrypt secrets in Git
3. **Add Sealed Secrets** - GitOps-friendly secret encryption
4. **Integrate cert-manager** - Automated TLS certificate management
5. **Add OPA/Gatekeeper** - Policy enforcement for secret usage

## Learning Objectives Achieved

✅ Understand Kubernetes native secrets (base64, etcd storage)  
✅ Implement secret volume mounts for hot-reload  
✅ Build automatic secret rotation system  
✅ Create audit trails for compliance  
✅ Design zero-downtime credential updates  
✅ Apply least privilege RBAC for secret access  
✅ Handle multiple secret types (API keys, DB, OAuth)  
✅ Implement production-grade error handling  
✅ Deploy monitoring for secrets operations  
✅ Scale secrets management to multi-tenant systems  

## Cleanup

```bash
./scripts/cleanup.sh
```

Removes:
- All deployed resources
- kind cluster
- Docker images (optional)

## References

- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- HashiCorp Vault: https://www.vaultproject.io/
- External Secrets Operator: https://external-secrets.io/
- Sealed Secrets: https://sealed-secrets.netlify.app/
- SOPS: https://github.com/mozilla/sops

## License

Educational use only. Not for production deployment without proper security review.
