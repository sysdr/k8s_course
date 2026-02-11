# Kubernetes Alerting with Alertmanager

Production-grade alert routing infrastructure demonstrating SLI/SLO-based alerting, multi-tier routing, and high-availability alert management.

## Quick Start

```bash
# 1. Build images
./scripts/build.sh

# 2. Setup cluster (kind/minikube)
./scripts/setup-cluster.sh

# 3. Deploy everything
./scripts/deploy.sh

# 4. Generate load
./scripts/load-test.sh
```

## Access Points

- **Grafana**: http://localhost:30300 (admin/admin)
- **Alertmanager**: http://localhost:30903
- **Prometheus**: `kubectl port-forward -n monitoring svc/prometheus 9090:9090`

## Architecture

The system consists of:
- 3 Python microservices (FastAPI + Kafka)
- React alert dashboard
- Prometheus + Alertmanager + Grafana
- Complete alert routing and SLO monitoring

## Testing Alerts

Trigger high error rate alert:
```bash
kubectl port-forward -n log-processing svc/log-ingestor 8080:8080

for i in {1..50}; do
  curl -X POST http://localhost:8080/ingest \
    -H "Content-Type: application/json" \
    -d '{
      "timestamp": '$(date +%s000)',
      "level": "ERROR",
      "service": "test-svc",
      "message": "Test error"
    }'
done
```

Check alerts in:
1. Prometheus UI → Alerts tab
2. Alertmanager UI → Alert groups
3. Grafana → Alerting Overview dashboard

See full documentation in lesson_article.md
