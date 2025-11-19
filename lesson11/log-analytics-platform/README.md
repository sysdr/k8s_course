# Log Analytics Platform - ConfigMaps & Secrets Demo

Production-ready Kubernetes log analytics system demonstrating ConfigMap and Secret management patterns.

## Architecture

- **log-collector**: Ingests logs via REST API, forwards to Kafka
- **log-processor**: Consumes from Kafka, processes and stores in PostgreSQL
- **log-api**: Query API for stored logs with Redis caching
- **frontend**: React dashboard for log visualization

## Key Patterns Demonstrated

### ConfigMaps
- Environment variable injection via `envFrom`
- Individual key references via `configMapKeyRef`
- Volume-mounted configuration files
- Environment-specific overlays

### Secrets
- Database credentials with proper RBAC
- Redis authentication
- API tokens
- stringData for readable secret creation

### Security
- RBAC policies restricting secret access by ServiceAccount
- Network policies for pod-to-pod communication
- Secret volume mounts with restricted permissions

## Quick Start

### Prerequisites
- Docker
- kubectl
- kind (for local cluster)

### Local Development with Docker Compose

```bash
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Build images
./scripts/build.sh

# Setup local cluster
./scripts/setup-cluster.sh

# Deploy
./scripts/deploy.sh
```

### Verify Configuration Injection

```bash
# Check ConfigMap values
kubectl get configmap log-processor-config -n log-analytics -o yaml

# Verify env injection
kubectl exec deploy/log-processor -n log-analytics -- env | grep DB_

# Check mounted config file
kubectl exec deploy/log-processor -n log-analytics -- cat /etc/config/config.yaml
```

### Test the System

```bash
# Send test log
curl -X POST http://localhost:8081/logs \
  -H "Content-Type: application/json" \
  -d '{"level": "INFO", "service": "test", "message": "Hello ConfigMaps!"}'

# Query logs
curl http://localhost:8080/logs

# View stats
curl http://localhost:8080/stats
```

## Configuration Management

### Updating ConfigMaps

```bash
# Update ConfigMap
kubectl edit configmap log-processor-config -n log-analytics

# Trigger rolling update to pick up changes
kubectl rollout restart deployment/log-processor -n log-analytics
```

### Secret Rotation

```bash
# Create new secret version
kubectl create secret generic database-credentials-v2 \
  --from-literal=DB_USER=log_processor \
  --from-literal=DB_PASSWORD=new-password \
  -n log-analytics

# Update deployment to use new secret
kubectl set env deployment/log-processor \
  --from=secret/database-credentials-v2 \
  -n log-analytics
```

## Production Considerations

1. **Enable etcd encryption** for Secrets at rest
2. **Use external secret management** (Vault, AWS Secrets Manager)
3. **Implement secret rotation** with dual-secret patterns
4. **Restrict RBAC** with `resourceNames` for specific secrets
5. **Monitor ConfigMap/Secret** changes with audit logs

## Directory Structure

```
log-analytics-platform/
├── src/
│   ├── log-collector/    # Ingestion service
│   ├── log-processor/    # Processing service
│   ├── log-api/          # Query API
│   └── frontend/         # React dashboard
├── k8s/
│   ├── base/             # Base manifests
│   └── overlays/         # Environment overlays
├── helm/                 # Helm charts
├── config/               # Configuration files
├── monitoring/           # Prometheus/Grafana
├── scripts/              # Operational scripts
└── tests/                # Integration tests
```

## Cleanup

```bash
./scripts/cleanup.sh        # Delete namespace
./scripts/cleanup.sh --full # Delete cluster
```
