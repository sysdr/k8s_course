# Global Log Processing Platform
### Kubernetes Odyssey — Lesson: Global Workload Distribution

Production-grade multi-region log ingestion and processing platform demonstrating:
- **Istio locality-aware load balancing** with automatic regional failover
- **HPA + VPA** autoscaling with topology spread constraints
- **Cross-cluster service federation** via ServiceEntry + mTLS
- **Full observability** with Prometheus, Grafana, and Jaeger

---

## Architecture

```
Clients (global)
     │  GeoDNS + Health Checks (ExternalDNS)
     ├──────────────────────────────┐
     ▼                              ▼
Istio Gateway (us-east)     Istio Gateway (eu-west)
     │                              │
     ▼                              ▼
Log Ingestion (HPA 3-12)    Log Ingestion (HPA 3-12)
     │                              │
     ▼                              ▼
 Kafka (3 brokers)          Kafka (3 brokers)
     │                              │
     ▼                              ▼
Log Processor (VPA)         Log Processor (VPA)
     │                              │
     ▼                              ▼
 PostgreSQL                   PostgreSQL
     │
     ▼ ServiceEntry (cross-cluster, mTLS)
Cross-Region Aggregator ──WebSocket──▶ React Dashboard
```

---

## Prerequisites

- Docker 24+
- kind 0.22+
- kubectl 1.28+
- Helm 3.12+
- istioctl 1.19+
- Python 3.11+
- Node.js 20+

---

## Quick Start (Local Development)

```bash
# 1. Start all services locally with Docker Compose
docker-compose up -d

# 2. Send test logs
curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{"service":"api-gateway","level":"INFO","message":"Request handled","trace_id":"abc-123"}'

# 3. Open dashboard
open http://localhost:3000
```

---

## Multi-Cluster Kubernetes Deployment

```bash
# Step 1: Provision kind clusters with topology labels
./scripts/setup-cluster.sh

# Step 2: Build and load images
./scripts/build.sh

# Step 3: Deploy to us-east
./scripts/deploy.sh us-east us-east-1

# Step 4: Deploy to eu-west
./scripts/deploy.sh eu-west eu-west-1

# Step 5: Set up monitoring
./scripts/monitoring-setup.sh kind-us-east

# Step 6: Run load test
./scripts/load-test.sh http://localhost:8000 60 20
```

---

## Testing Failover

```bash
# Simulate us-east node failure
kubectl --context kind-us-east drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Watch Istio reroute traffic to eu-west (check Grafana 'Traffic Distribution' dashboard)
kubectl --context kind-us-east get events -n log-processing --watch

# Watch HPA scale up in eu-west under increased load
kubectl --context kind-eu-west get hpa -n log-processing -w
```

---

## Key Configuration Files

| File | Purpose |
|---|---|
| `k8s/istio/destinationrule.yaml` | Locality-aware LB + outlier detection |
| `k8s/istio/serviceentry-crosscluster.yaml` | Cross-cluster endpoint federation |
| `k8s/base/log-ingestion/hpa.yaml` | CPU/memory-based autoscaling |
| `k8s/base/log-processor/vpa.yaml` | Vertical autoscaling for processor |
| `k8s/base/network-policies/netpol.yaml` | Zero-trust network isolation |
| `monitoring/prometheus/alert-rules.yaml` | Production alert definitions |
| `helm/log-platform/values.yaml` | Environment-specific configuration |

---

## Observability

```bash
# Grafana dashboard
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# → http://localhost:3000 (admin/admin123)

# Jaeger tracing
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
# → http://localhost:16686

# Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

---

## Troubleshooting

**Pods stuck in Pending:**
Check topology spread constraints — if `DoNotSchedule` is set and zones are imbalanced, add nodes or change to `ScheduleAnyway`.

**Istio mTLS failures:**
Verify PeerAuthentication mode and that both namespaces have `istio-injection: enabled`.

**High Kafka consumer lag:**
Increase log-processor replicas or review VPA recommendations. Check for slow DB writes under `db_batch_write_seconds` metric.

**Cross-cluster ServiceEntry unreachable:**
Confirm the eu-west LoadBalancer IP in `serviceentry-crosscluster.yaml` is correct and firewalls permit port 8000.
