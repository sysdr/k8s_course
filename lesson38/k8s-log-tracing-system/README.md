# Log Tracing System — Kubernetes Production Reference

Lesson 38 of *The Kubernetes Odyssey*: end-to-end distributed tracing with Jaeger, OpenTelemetry, and Istio.

---

## Architecture at a Glance

```
Client → Ingress / Istio Gateway
           ↓
     Log Ingestor (FastAPI)
       ↓ HTTP        ↓ Kafka (traceparent)
 Log Processor   Log Processor (consumer)
       ↓                  ↓
  PostgreSQL         Redis / Analytics Svc
                          ↓
                    React Dashboard (WebSocket)

Observability plane (all services → OTel Collector → Jaeger):
  Prometheus ← /metrics   │   Grafana ← Prometheus + Jaeger + Loki
```

---

## Prerequisites

| Tool | Min Version |
|------|-------------|
| Docker | 24+ |
| kind | 0.21+ |
| kubectl | 1.28+ |
| helm | 3.12+ |
| istioctl | 1.19+ |
| Python | 3.11+ |

---

## Quick Start (local, ~15 min)

```bash
# 1. Generate project (you are here)
bash generate_k8s_system.sh

# 2. Create kind cluster + load images
cd k8s-log-tracing-system
bash scripts/setup-cluster.sh

# 3. Deploy everything
bash scripts/deploy.sh

# 4. Verify pods are Running
kubectl get pods -n app -w

# 5. Open the dashboard
kubectl port-forward svc/frontend 8080:80 -n app
# → http://localhost:8080

# 6. Generate load
bash scripts/load-test.sh http://localhost:8000/ingest

# 7. View traces
kubectl port-forward svc/jaeger-query 16686:16686 -n observability
# → http://localhost:16686

# 8. View dashboards
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n observability
# → http://localhost:3000  (admin / changeme)
```

---

## Local Development (no Kubernetes)

```bash
docker compose up -d
# All services + Kafka + Redis + Postgres + Jaeger start locally.
# Jaeger UI: http://localhost:16686
# Ingestor:  http://localhost:8000
```

---

## Key Architectural Decisions

### Why DaemonSet for the OTel Collector?
A DaemonSet places one Collector per node.  Application pods talk to the Collector on the same node via localhost — zero network hop for telemetry export.  This keeps trace export latency sub-millisecond and eliminates a cross-node TCP connection for every span batch.

### Why LEAST_CONN instead of ROUND_ROBIN?
The Processor's per-request cost varies (DB queries range 1–50 ms).  LEAST_CONN routes new requests to the pod with the fewest active connections, naturally balancing variable-cost workloads.  ROUND_ROBIN is optimal only when every request costs the same.

### Why PDBs with minAvailable=1 instead of maxUnavailable=0?
`maxUnavailable=0` blocks *all* voluntary evictions — node upgrades stall.  `minAvailable=1` with 2 replicas lets Kubernetes evict one pod at a time while guaranteeing at least one is always serving.

### Why tail_sampling in the Collector, not head_sampling in the SDK?
Head sampling decides *before* the request completes: you cannot know if it will error.  Tail sampling waits for the full trace to arrive, checks for errors or latency outliers, and then decides to keep or drop.  This is why the Collector config keeps 100 % of ERROR traces regardless of the global 10 % rate.

---

## Monitoring & Observability

| Signal | Tool | How to access |
|--------|------|---------------|
| Metrics | Prometheus | port-forward 9090 |
| Dashboards | Grafana | port-forward 3000 |
| Traces | Jaeger | port-forward 16686 |
| Logs | Loki (L37) | via Grafana Loki datasource |
| Alerts | Alertmanager (L39) | port-forward 9093 |

---

## Helm Usage

```bash
# Install
helm install log-tracing ./helm/log-tracing-system -n app --create-namespace

# Upgrade with new image tags
helm upgrade log-tracing ./helm/log-tracing-system -n app \
  --set logIngestor.image.tag=abc123 \
  --set logProcessor.image.tag=abc123

# Lint
helm lint ./helm/log-tracing-system
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Traces disappear at Kafka boundary | traceparent not injected in producer | Check `kafka_producer.py` → `inject(carrier=headers)` |
| Pods stuck in Pending | Resource requests exceed node capacity | Reduce `resources.requests` or add nodes |
| Jaeger shows orphan spans | Consumer not extracting context | Verify `extract_context_from_headers` in `consumer.py` |
| HPA not scaling | Metrics server not installed | `kubectl apply -f https://github.com/kubernetes/metrics-server/...` |
| NetworkPolicy blocks traffic | Default-deny active, allow rule missing | Add a NetworkPolicy allow rule for the specific flow |

---

## Teardown

```bash
bash scripts/cleanup.sh
```

---

*Lesson 38 — The Kubernetes Odyssey.  Next: Lesson 39 — Alerting with Alertmanager.*
