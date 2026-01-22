# Kubernetes Logging System with Loki Stack

Production-grade distributed logging infrastructure using Loki, Promtail, and Grafana.

## Architecture Overview

This system demonstrates enterprise-level log aggregation patterns:

- **Loki**: Cost-efficient log aggregation with label-based indexing
- **Promtail**: DaemonSet-based log collection from all pods
- **Grafana**: Unified observability platform for logs and metrics
- **Microservices**: Three FastAPI services with structured JSON logging
- **React Dashboard**: Real-time log visualization and analytics

## Key Features

### Production Patterns
- ✅ Structured JSON logging with correlation IDs
- ✅ Label-based log indexing (10x cost reduction vs ELK)
- ✅ High-availability Loki deployment
- ✅ DaemonSet log collection across all nodes
- ✅ Horizontal pod autoscaling based on metrics
- ✅ Pod disruption budgets for high availability
- ✅ Resource limits and security contexts

### Observability Stack
- **Logs**: Loki with 30-day retention
- **Metrics**: Prometheus integration
- **Dashboards**: Grafana with pre-configured datasources
- **Correlation**: Request tracing with correlation IDs

## Prerequisites

- Docker Desktop or Docker Engine
- kind (Kubernetes in Docker) or minikube
- kubectl (Kubernetes CLI)
- 8GB RAM minimum

## Quick Start

### 1. Build Docker Images

```bash
./scripts/build.sh
```

This builds:
- api-gateway:latest
- order-service:latest
- payment-service:latest
- logging-dashboard:latest

### 2. Create Kubernetes Cluster

```bash
./scripts/setup-cluster.sh
```

Creates a 3-node kind cluster with images pre-loaded.

### 3. Deploy Logging Stack

```bash
./scripts/deploy.sh
```

Deploys:
- Loki StatefulSet
- Promtail DaemonSet
- Grafana
- All microservices

### 4. Access Grafana

```bash
kubectl port-forward -n logging-system svc/grafana 3000:3000
```

Open http://localhost:3000
- Username: `admin`
- Password: `admin123`

### 5. Generate Test Logs

```bash
./scripts/load-test.sh
```

Sends 100 orders to generate realistic log traffic.

## Exploring Logs in Grafana

### Navigate to Explore
1. Click "Explore" in the left sidebar
2. Select "Loki" as the datasource

### Example LogQL Queries

**All logs from API Gateway:**
```
{namespace="logging-system",service="api-gateway"}
```

**Error logs across all services:**
```
{namespace="logging-system",severity="error"}
```

**Logs for a specific correlation ID:**
```
{namespace="logging-system"} |= "correlation_id=abc-123"
```

**Order creation events:**
```
{namespace="logging-system",service="order-service"} | json | event="order_created"
```

**Payment failures:**
```
{namespace="logging-system",service="payment-service"} | json | status="declined"
```

**Error rate by service (5min windows):**
```
sum(rate({namespace="logging-system",severity="error"}[5m])) by (service)
```

## System Components

### Microservices

**API Gateway** (Port 8000)
- Routes requests to downstream services
- Generates correlation IDs
- Logs all HTTP requests/responses

**Order Service** (Port 8001)
- Handles order creation
- Business event logging
- In-memory order storage

**Payment Service** (Port 8002)
- Processes payments
- Audit logging for compliance
- Simulates payment gateway

### Logging Stack

**Loki**
- Log aggregation and storage
- Label-based indexing
- 30-day retention
- Resource: 512Mi-2Gi memory

**Promtail**
- Runs as DaemonSet on every node
- Collects container logs from /var/log/pods
- Parses JSON logs and extracts labels
- Forwards to Loki

**Grafana**
- Log visualization
- LogQL query interface
- Pre-configured Loki datasource

## Log Format

All services use structured JSON logging:

```json
{
  "timestamp": "2026-01-12T10:30:00.123456Z",
  "level": "info",
  "event": "order_created",
  "correlation_id": "abc-123-def-456",
  "service": "order-service",
  "order_id": "ORD-123",
  "customer_id": "CUST-456",
  "amount": 99.99
}
```

## Scaling Configuration

### Horizontal Pod Autoscaling
- **API Gateway**: 3-10 replicas (CPU: 70%, Memory: 80%)
- **Order Service**: 2-8 replicas (CPU: 70%)
- **Payment Service**: 2-6 replicas (CPU: 70%)

### Loki Scaling
For production scale (>1TB/day):
- Increase Loki replicas to 3+
- Use object storage (S3/GCS) instead of local filesystem
- Deploy separate ingester, distributor, and querier components

### Promtail Resource Limits
- Per node: 128Mi-512Mi memory
- Handles 10K logs/second per node

## Monitoring

### Key Metrics

**Loki Health:**
```bash
kubectl port-forward -n logging-system svc/loki 3100:3100
curl http://localhost:3100/ready
```

**Promtail Status:**
```bash
kubectl get daemonset -n logging-system promtail
```

**Service Metrics:**
```bash
kubectl port-forward -n logging-system svc/api-gateway 8000:8000
curl http://localhost:8000/metrics
```

### Prometheus Integration

The system is ready for Prometheus integration:
- All services expose `/metrics` endpoints
- Loki provides metrics on `:3100/metrics`
- Promtail exposes metrics on `:3101/metrics`

## Troubleshooting

### Loki Not Receiving Logs

**Check Promtail logs:**
```bash
kubectl logs -n logging-system -l app=promtail --tail=50
```

**Verify Promtail can reach Loki:**
```bash
kubectl exec -n logging-system -it <promtail-pod> -- wget -O- http://loki:3100/ready
```

### Services Not Logging

**Check service logs:**
```bash
kubectl logs -n logging-system -l app=api-gateway --tail=50
```

**Verify JSON format:**
```bash
kubectl logs -n logging-system -l app=api-gateway --tail=1 | jq .
```

### Grafana Can't Query Logs

**Test Loki directly:**
```bash
kubectl port-forward -n logging-system svc/loki 3100:3100
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={namespace="logging-system"}' \
  --data-urlencode 'limit=10' | jq .
```

### High Memory Usage

**Loki ingester memory:**
- Increase memory limits in statefulset.yaml
- Decrease `ingestion_burst_size_mb` in Loki config
- Enable compaction more frequently

**Promtail memory:**
- Reduce `readline_rate` in Promtail config
- Add more aggressive filtering in pipeline stages

## Production Considerations

### Security
- [ ] Enable authentication in Loki
- [ ] Use TLS for Loki-Promtail communication
- [ ] Implement RBAC for Grafana users
- [ ] Mask sensitive data in logs (PII, secrets)

### Retention
- Current: 30 days (720h)
- Adjust `retention_period` in Loki config
- Implement tiered storage (hot/warm/cold)

### High Availability
- [ ] Deploy Loki in microservices mode (separate distributors, ingesters, queriers)
- [ ] Use external object storage (S3, GCS)
- [ ] Deploy multiple Grafana replicas with shared database
- [ ] Implement Loki query frontend for caching

### Performance
- [ ] Use SSD storage for Loki
- [ ] Tune `max_look_back_period` based on query patterns
- [ ] Enable query result caching
- [ ] Optimize label cardinality (5-8 labels max)

### Cost Optimization
- [ ] Implement aggressive compaction
- [ ] Use cheaper storage tiers for old logs
- [ ] Set appropriate retention policies per namespace
- [ ] Monitor and optimize label cardinality

## Cleanup

### Delete Resources
```bash
./scripts/cleanup.sh
```

### Delete Cluster
```bash
kind delete cluster --name logging-demo
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  API Gateway │  │Order Service │  │Payment Service│     │
│  │   (Pod x3)   │  │  (Pod x2)    │  │  (Pod x2)     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘     │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                           │                                 │
│                    JSON Logs (stdout)                       │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │       Promtail DaemonSet          │              │
│         │  (Runs on every Kubernetes node)  │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                 │
│                      gRPC/HTTP                              │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │      Loki StatefulSet             │              │
│         │   - Distributor (ingestion)       │              │
│         │   - Ingester (buffering)          │              │
│         │   - Querier (queries)             │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                 │
│                  Persistent Volume                          │
│                   (Log Storage)                             │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │         Grafana                   │              │
│         │   - LogQL Queries                 │              │
│         │   - Dashboards                    │              │
│         │   - Alerting                      │              │
│         └───────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Real-World Patterns

This implementation follows patterns from:

- **Uber**: Label-based log aggregation for 100TB/day
- **Shopify**: Cost optimization (70% reduction vs ELK)
- **Netflix**: Correlation IDs for distributed tracing
- **Spotify**: Structured logging across 3000+ microservices

## Next Steps

- **Lesson 38**: Add distributed tracing with Jaeger
- Integrate with Prometheus for unified observability
- Implement log-based alerting
- Add log-to-metrics conversion
- Deploy in production with external object storage

## Support

For issues or questions:
- Review logs: `kubectl logs -n logging-system <pod-name>`
- Check status: `kubectl get all -n logging-system`
- Loki docs: https://grafana.com/docs/loki/latest/
- Course materials: [Kubernetes Odyssey]

---

**Built with:**
- Loki 2.9.3
- Promtail 2.9.3
- Grafana 10.2.2
- Python 3.11 / FastAPI
- React 18 / Material-UI
- Kubernetes 1.28+
