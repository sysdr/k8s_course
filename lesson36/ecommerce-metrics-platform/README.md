# E-Commerce Analytics Platform - Prometheus Metrics Implementation

Production-ready Kubernetes system demonstrating metrics-driven autoscaling and observability patterns used by companies like Netflix, Spotify, and Shopify.

## System Architecture
```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Frontend   │────▶│  Order Service  │────▶│ Payment Service  │
│  (React/TS)  │     │  (Python/Fast   │     │     (Go)         │
│              │     │      API)       │     │                  │
└──────────────┘     └─────────────────┘     └──────────────────┘
       │                     │                         │
       │                     │                         │
       ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus Operator                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ServiceMonitor│  │ PrometheusRule│  │AlertManager │      │
│  │  (Discovery)  │  │ (Rules/Alerts)│  │ (Routing)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Grafana    │
                    │  Dashboards  │
                    └──────────────┘
```

## Key Features

### 1. **Prometheus Operator Pattern**
- Declarative monitoring configuration using CRDs
- Automatic target discovery with ServiceMonitors
- Dynamic configuration regeneration

### 2. **Custom Metrics for Autoscaling**
- Business metrics drive HPA (not just CPU/memory)
- Queue depth monitoring for proactive scaling
- P99 latency tracking for SLO enforcement

### 3. **Production Alert Pipeline**
- Multi-tier severity routing (Slack, PagerDuty)
- Alert suppression to prevent fatigue
- Contextual runbooks for faster MTTR

### 4. **Recording Rules for Performance**
- Pre-computed expensive queries
- Reduces dashboard load time by 95%
- Enables real-time SLO tracking

## Quick Start

### Prerequisites
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured
- Helm 3.12+
- Docker

### Build and Deploy
```bash
# 1. Build Docker images
./scripts/deployment/build-images.sh

# 2. Load images to cluster (for kind/minikube)
kind load docker-image order-service:latest payment-service:latest frontend:latest

# 3. Deploy everything
./scripts/deployment/deploy-all.sh

# 4. Verify deployment
kubectl get pods -n ecommerce
kubectl get servicemonitors -n ecommerce
```

### Access Services
```bash
# Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Open: http://localhost:9090

# Grafana dashboards
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open: http://localhost:3000 (admin/admin)

# Frontend application
kubectl port-forward -n ecommerce svc/frontend 8080:80
# Open: http://localhost:8080
```

## Testing Metrics-Driven Autoscaling

### Generate Load
```bash
# Port forward order service
kubectl port-forward -n ecommerce svc/order-service 8000:8000

# Run load test (100 RPS for 5 minutes)
./scripts/testing/load-test.sh http://localhost:8000 300 100
```

### Observe Autoscaling
```bash
# Watch HPA in action
kubectl get hpa -n ecommerce -w

# Check pod scaling
kubectl get pods -n ecommerce -w

# View custom metrics
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/ecommerce/pods/*/order_queue_depth"
```

## Key PromQL Queries

### Order Processing Rate
```promql
# Orders per second by status
sum(rate(orders_total[5m])) by (status)

# Error rate
sum(rate(orders_total{status="failed"}[5m])) / sum(rate(orders_total[5m]))
```

### Latency Analysis
```promql
# P99 latency
histogram_quantile(0.99, sum(rate(order_processing_duration_seconds_bucket[5m])) by (le))

# Latency by endpoint
histogram_quantile(0.99, sum(rate(order_processing_duration_seconds_bucket[5m])) by (endpoint, le))
```

### Business Metrics
```promql
# Revenue per minute
sum(rate(order_value_total_dollars[1m]))

# Average order value
sum(rate(order_value_total_dollars[5m])) / sum(rate(orders_total[5m]))
```

### Capacity Planning
```promql
# CPU throttling rate
rate(container_cpu_cfs_throttled_seconds_total{namespace="ecommerce"}[5m])

# Memory usage percentage
(container_memory_working_set_bytes / container_spec_memory_limit_bytes) * 100
```

## Production Patterns Demonstrated

### 1. **ServiceMonitor Pattern**
Automatic monitoring configuration for new services:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: order-service-monitor
spec:
  selector:
    matchLabels:
      app: order-service
  endpoints:
  - port: http
    interval: 15s
```

### 2. **Recording Rules**
Pre-compute expensive aggregations:
```yaml
- record: job:order_processing_duration:p99
  expr: histogram_quantile(0.99, sum(rate(order_processing_duration_seconds_bucket[5m])) by (job, le))
```

### 3. **Custom Metrics HPA**
Scale on business metrics:
```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: order_queue_depth
    target:
      averageValue: "50"
```

### 4. **Multi-Tier Alerting**
Context-aware alert routing:
```yaml
routes:
- match:
    severity: critical
  receiver: pagerduty-critical
- match:
    severity: warning
  receiver: slack-notifications
```

## Troubleshooting

### Metrics Not Appearing
```bash
# Check ServiceMonitor is created
kubectl get servicemonitors -n ecommerce

# Verify Prometheus is scraping targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Go to: http://localhost:9090/targets

# Check pod annotations
kubectl get pod -n ecommerce -o yaml | grep prometheus
```

### HPA Not Scaling
```bash
# Check HPA status
kubectl describe hpa order-service-hpa -n ecommerce

# Verify custom metrics API
kubectl get apiservices | grep metrics

# Check metrics-server is running
kubectl get pods -n kube-system | grep metrics-server
```

### High Cardinality Issues
```bash
# Find high cardinality metrics
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data | length'

# Check time series count
curl http://localhost:9090/api/v1/status/tsdb | jq '.data.seriesCountByMetricName'
```

## Architecture Insights

### Why Pull-Based Metrics?
- **Failure Detection**: Missing scrapes indicate target problems
- **Backpressure Control**: Prometheus controls load, not targets
- **Centralized Config**: No changes needed to application deployments

### Cardinality Management
- Keep label combinations under 10,000 per metric
- Use high-cardinality data in logs, not metrics
- Apply recording rules for pre-aggregation

### Alert Fatigue Prevention
- Implement multi-tier escalation (warning → critical → emergency)
- Use alert suppression windows (15-minute silence for repeats)
- Context-aware routing (team-specific receivers)

## Production Checklist

- [ ] ServiceMonitors created for all services
- [ ] Recording rules configured for expensive queries
- [ ] Alert rules aligned with SLOs
- [ ] PodDisruptionBudgets set for high availability
- [ ] HPA configured with custom metrics
- [ ] Network policies restrict metric endpoint access
- [ ] Grafana dashboards imported
- [ ] AlertManager receivers configured
- [ ] Long-term storage (Thanos/Cortex) planned
- [ ] Retention policies set appropriately

## Scaling to Production

### Multi-Cluster Federation
```
Regional Prometheus → Thanos Sidecar → S3 → Global Thanos Query
```

### Long-Term Retention Strategy
```
0-7 days:   Full resolution (15s)
7-30 days:  5m downsampling (95% storage reduction)
30-365 days: 1h downsampling (cold storage, S3)
```

### Cost Optimization
- Use recording rules to reduce query CPU
- Implement retention policies (30d for full res)
- Apply relabeling to drop unnecessary labels
- Consider VictoriaMetrics for better compression

## Learning Outcomes

After completing this system, you can:
1. Configure Prometheus Operator for declarative monitoring
2. Implement custom metrics for HPA autoscaling
3. Design multi-tier alert pipelines with contextual routing
4. Use recording rules to optimize query performance
5. Troubleshoot high cardinality and retention issues
6. Apply production patterns from FAANG companies

## References

- [Prometheus Operator Documentation](https://prometheus-operator.dev/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Netflix Observability Blog](https://netflixtechblog.com/)
- [Spotify Monitoring Architecture](https://engineering.atspotify.com/)
- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)

## Cleanup
```bash
./scripts/maintenance/cleanup.sh
```

---

**License**: MIT  
**Author**: Senior Platform Engineer  
**Course**: The Kubernetes Odyssey - Lesson 36
