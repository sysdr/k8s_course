# Log Platform — Production Kubernetes System

A production-grade, multi-service log processing platform demonstrating advanced Kubernetes patterns including HPA, PDB, multi-cluster failover, and full observability.

## Architecture

```
Internet
  │
  ▼
Ingress / Load Balancer
  │
  ├── /api/ingest → log-ingestion (FastAPI, 3-20 pods, HPA)
  │        └──► Kafka → log-processor (2-5 pods)
  │                         └──► Postgres (StatefulSet)
  │                         └──► Redis (cache)
  │
  ├── /api/logs  → log-query (FastAPI, 2-10 pods, HPA)
  │        ├──► Postgres (read)
  │        └──► Redis (cache)
  │
  └── /         → frontend (React, nginx, 2 pods)
```

**Services:**
- `log-ingestion` — Accepts log events via HTTP, publishes to Kafka
- `log-processor` — Kafka consumer, persists to Postgres, caches in Redis
- `log-query` — REST query API over stored logs with Redis caching
- `frontend` — React dashboard for log analytics

## Prerequisites

- Docker 24+
- kubectl 1.28+
- helm 3.12+
- kind 0.22+ (for local cluster)
- AWS CLI (for DNS failover tests)

## Quick Start (Local)

### 1. Generate the full project
```bash
chmod +x generate_k8s_system.sh
./generate_k8s_system.sh
cd k8s-log-platform
```

### 2. Start local development with Docker Compose
```bash
docker-compose up -d
# Services available:
# log-ingestion: http://localhost:8000
# log-query:     http://localhost:8001
# frontend:      http://localhost:3000
```

### 3. Create local Kubernetes cluster
```bash
./scripts/setup-cluster.sh
```

### 4. Build images
```bash
./scripts/build.sh
```

### 5. Deploy to local cluster
```bash
ENVIRONMENT=us-east-1 ./scripts/deploy.sh
```

## Production Deployment

### Deploy with Helm
```bash
# Add dependencies
helm dependency update helm/log-platform/

# Install
helm upgrade --install log-platform helm/log-platform/ \
  --namespace log-platform --create-namespace \
  --set global.environment=production \
  --set global.region=us-east-1 \
  -f helm/log-platform/values.yaml

# Watch rollout
kubectl rollout status deployment/log-ingestion -n log-platform
```

### Deploy with Kustomize
```bash
kubectl apply -k k8s/overlays/us-east-1/
```

## Break-It-Friday: Failover Test

```bash
# Configure your cluster contexts and DNS zone
export PRIMARY_CTX=cluster-us-east
export FAILOVER_CTX=cluster-eu-west
export DNS_ZONE_ID=Z1234567890ABC
export API_HOST=api.yourdomain.com

chmod +x scripts/failover-test.sh
./scripts/failover-test.sh
```

The script will:
1. Cordon + drain all application pods in the primary cluster
2. Watch the failover cluster stabilize
3. Update Route53 DNS to point at the failover LoadBalancer
4. Measure and report actual RTO
5. Restore the primary cluster on your signal

## Monitoring

```bash
# Grafana (admin/admin123)
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3001:80

# Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090

# Jaeger tracing
kubectl port-forward -n monitoring svc/log-platform-jaeger-query 16686:16686
```

## Load Testing

```bash
cd tests/load
pip install -r requirements.txt
locust -f locustfile.py --host=http://localhost:8000 \
  --users=100 --spawn-rate=10 --run-time=5m
```

## Key Kubernetes Patterns Demonstrated

| Pattern | Resource | Purpose |
|---------|----------|---------|
| HPA | `hpa/hpa.yaml` | CPU/Memory-based pod autoscaling |
| PDB | `pdb/pdb.yaml` | Minimum availability during disruptions |
| preStop sleep | Deployments | Graceful connection draining |
| minReadySeconds | Deployments | Warm-up window before traffic routing |
| TopologySpread | Deployments | Even pod distribution across nodes |
| NetworkPolicy | `networkpolicies/netpol.yaml` | Zero-trust pod networking |
| GitOps Overlays | `k8s/overlays/` | Environment-specific config without duplication |

## Troubleshooting

**Pods stuck in Pending:**
```bash
kubectl describe pod <pod> -n log-platform
# Check: resource requests vs node capacity, taints/tolerations
```

**PDB blocking drain during failover test:**
```bash
kubectl get pdb -n log-platform
kubectl patch pdb log-ingestion-pdb -n log-platform \
  --type=json -p='[{"op":"replace","path":"/spec/minAvailable","value":0}]'
# Remember to restore after test
```

**Readiness probe failing post-deployment:**
```bash
kubectl describe pod <pod> -n log-platform | grep -A10 "Readiness"
kubectl logs <pod> -n log-platform --previous
# Check ConfigMap env vars point to the correct region endpoints
```

**Service connectivity:**
```bash
kubectl exec -n log-platform <pod> -- curl -v http://log-query/healthz
# Check NetworkPolicy and service DNS if connectivity fails
```
