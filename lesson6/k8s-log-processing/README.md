# Kubernetes Log Processing System

Production-grade distributed log processing demonstrating advanced Kubernetes patterns.

## Architecture

- **Log Ingestion API**: FastAPI with Kafka producer and Redis cache
- **Log Processor Workers**: Kafka consumers writing to TimescaleDB
- **Analytics Dashboard**: React dashboard for visualization
- **Data Layer**: TimescaleDB, Kafka, Redis

## Quick Start

```bash
# Setup cluster
./scripts/setup-cluster.sh

# Build images
./scripts/build.sh

# Deploy
./scripts/deploy.sh

# Test
curl -X POST http://localhost:8080/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{"level":"INFO","service":"test","message":"Hello"}'
```

## Key Features

- **Autoscaling**: HPA based on CPU/memory (3-20 replicas for API, 2-15 for workers)
- **High Availability**: PodDisruptionBudgets ensure minimum replicas during updates
- **Service Mesh**: Istio provides mTLS, traffic management, observability
- **Monitoring**: Prometheus + Grafana + Jaeger for complete observability
- **StatefulSets**: TimescaleDB with persistent 10Gi volumes
- **Network Policies**: Least-privilege pod communication

## Monitoring

```bash
# Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Jaeger
kubectl port-forward -n istio-system svc/tracing 16686:80
```

## Cleanup

```bash
./scripts/cleanup.sh
```

## Learning Outcomes

- Kubernetes orchestration patterns (Deployments, StatefulSets, Services)
- Autoscaling (HPA with multiple metrics)
- High availability (PDB, readiness/liveness probes)
- Service mesh (Istio traffic management, mTLS, observability)
- Monitoring (Prometheus metrics, Grafana dashboards, distributed tracing)
- Security (NetworkPolicies, RBAC, pod security)
