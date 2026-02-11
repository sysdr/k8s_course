# Break-It-Friday: Observability Stack Debugging

Production-grade Kubernetes system for learning observability debugging patterns. This project intentionally creates a broken monitoring stack where Grafana shows "No Data", then provides diagnostic tools to identify and fix the issues.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Observability Stack (Monitoring Namespace)                 │
│                                                              │
│  ┌──────────┐      ┌─────────────┐      ┌──────────┐      │
│  │ Grafana  │◄─────│ Prometheus  │◄─────│AlertMgr  │      │
│  └──────────┘      └─────────────┘      └──────────┘      │
│                           ▲                                 │
│                           │ ServiceMonitor Discovery        │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ Scrape /metrics
┌───────────────────────────┼─────────────────────────────────┐
│  Application Namespace (Default)                            │
│                           │                                  │
│  ┌────────────────────────▼───────────────┐                │
│  │   Log Processor (FastAPI)              │                │
│  │   - Port 8000: HTTP API                │                │
│  │   - Port 8080: Prometheus /metrics     │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌─────────────────────────────────────────┐               │
│  │   Metrics Exporter                       │               │
│  │   - Port 8081: Custom business metrics   │               │
│  └─────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker
- kind or minikube
- kubectl
- Helm 3
- Python 3.11+

### Setup

```bash
# 1. Create local Kubernetes cluster
./scripts/deployment/setup-cluster.sh

# 2. Build container images
./scripts/deployment/build.sh

# 3. Deploy BROKEN scenario (for debugging exercise)
./scripts/deployment/deploy-broken-scenario.sh

# 4. Port-forward services
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &
kubectl port-forward -n monitoring svc/kube-prometheus-prometheus 9090:9090 &
kubectl port-forward svc/log-processor 8000:80 &

# 5. Run diagnostics
python3 scripts/diagnostics/check-observability-stack.py
```

### Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application**: http://localhost:8000

## Debugging Exercise

### Expected Issues in Broken Scenario

1. **Grafana shows "No Data"** for all dashboards
2. **Prometheus Targets page** shows zero targets for log-processor
3. **Metrics queries** return empty results

### Root Causes (Don't Peek!)

<details>
<summary>Click to reveal issues</summary>

1. **ServiceMonitor missing required label**: Prometheus serviceMonitorSelector requires `team: platform` label
2. **ServiceMonitor selector mismatch**: Selector uses wrong labels that don't match Service
3. **Port name mismatch**: ServiceMonitor references `http` port instead of `metrics` port
4. **Namespace isolation**: RBAC permissions may be missing for cross-namespace scraping

</details>

### Diagnostic Steps

1. **Run automated diagnostics**:
   ```bash
   python3 scripts/diagnostics/check-observability-stack.py
   ```

2. **Check Prometheus targets**:
   ```bash
   # Open Prometheus UI
   open http://localhost:9090/targets
   
   # Should show zero log-processor targets in broken scenario
   ```

3. **Verify ServiceMonitor discovery**:
   ```bash
   kubectl get servicemonitor -n default -o yaml
   kubectl describe servicemonitor log-processor-broken -n default
   ```

4. **Check Service labels**:
   ```bash
   kubectl get service log-processor -n default -o yaml
   ```

5. **Test metrics endpoint directly**:
   ```bash
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
     curl http://log-processor.default.svc.cluster.local:8080/metrics
   ```

### Fix and Deploy

Once you've identified issues:

```bash
# Apply the fixed ServiceMonitor
./scripts/deployment/deploy-fixed-scenario.sh

# Verify fixes
python3 scripts/diagnostics/check-observability-stack.py

# Should see metrics in Grafana within 30 seconds
```

## Component Deep Dive

### Log Processor Service

FastAPI application that:
- Exposes HTTP API on port 8000
- Exports Prometheus metrics on port 8080
- Tracks request duration, log processing rates, error counts
- Generates realistic synthetic load for testing

**Key Metrics**:
- `http_request_duration_seconds`: Request latency histogram
- `log_entries_processed_total`: Counter of processed logs by severity/source
- `active_processing_jobs`: Gauge of concurrent processing jobs
- `log_parse_errors_total`: Counter of parsing failures

### ServiceMonitor Configuration

Critical fields for debugging:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    team: platform  # MUST match Prometheus serviceMonitorSelector
spec:
  selector:
    matchLabels:
      app: log-processor  # MUST match Service labels exactly
      component: backend
  endpoints:
  - port: metrics  # MUST match Service port NAME (not number)
    interval: 15s
    path: /metrics
```

### Prometheus Discovery Flow

1. Prometheus Operator watches ServiceMonitor CRDs
2. Matches ServiceMonitors with `team: platform` label (configured in values.yaml)
3. For each matched ServiceMonitor, finds Services matching selector
4. For each matched Service, finds Endpoints (pod IPs)
5. Generates scrape configuration dynamically
6. Scrapes metrics from pod IPs on specified port

**Failure points**:
- ServiceMonitor missing required labels → Not discovered
- Selector mismatch → No Services matched
- Port name wrong → Scrapes wrong endpoint (gets HTML instead of metrics)
- RBAC missing → Can't list Endpoints

## Production Patterns

### High-Cardinality Defense

```yaml
# Drop high-cardinality labels before ingestion
metricRelabelings:
- sourceLabels: [user_id]
  action: labeldrop
- sourceLabels: [request_id]
  action: labeldrop
```

### Multi-Tier Scraping

For large clusters, implement hierarchical scraping:
- Edge Prometheus: Scrape application pods (15s interval)
- Aggregation Prometheus: Scrape edge Prometheus (30s interval)
- Global Thanos: Query federation across regions

### Graceful Degradation

```yaml
# Grafana datasource with failover
datasources:
- name: Prometheus Primary
  url: http://prometheus-primary:9090
- name: Prometheus Secondary
  url: http://prometheus-secondary:9090
```

## Load Testing

Generate realistic traffic:

```bash
# Terminal 1: Port-forward application
kubectl port-forward svc/log-processor 8000:80

# Terminal 2: Generate load
python3 scripts/load-testing/generate-load.py

# Monitor metrics in Grafana
open http://localhost:3000
```

## Troubleshooting Guide

### Grafana Shows "No Data"

**Diagnosis**:
1. Check Grafana datasource health: Settings → Data Sources → Prometheus → Save & Test
2. Verify Prometheus is running: `kubectl get pods -n monitoring`
3. Check Prometheus targets: http://localhost:9090/targets
4. Verify metrics exist: Execute query in Prometheus UI

**Common fixes**:
- Datasource URL incorrect → Update to `http://prometheus-operated:9090`
- Query syntax error → Test in Prometheus UI first
- Time range too far back → Adjust dashboard time range

### Prometheus Shows Zero Targets

**Diagnosis**:
```bash
# Check ServiceMonitor labels
kubectl get servicemonitor -n default -o yaml

# Check Prometheus serviceMonitorSelector
kubectl get prometheus -n monitoring -o yaml | grep -A5 serviceMonitorSelector
```

**Common fixes**:
- Add missing label: `kubectl label servicemonitor <name> team=platform`
- Fix selector: Update ServiceMonitor spec.selector.matchLabels
- Apply correct ServiceMonitor: `kubectl apply -f k8s/overlays/fixed/`

### Targets Exist But Are Down

**Diagnosis**:
```bash
# Check pod health
kubectl get pods -l app=log-processor

# Check metrics endpoint
kubectl port-forward <pod-name> 8080:8080
curl http://localhost:8080/metrics

# Check Service endpoints
kubectl get endpoints log-processor
```

**Common fixes**:
- Pod crash looping → Check logs: `kubectl logs <pod>`
- Port mismatch → Verify Service and Pod port numbers match
- Metrics not exposed → Check application code

## Learning Outcomes

After completing this exercise, you should understand:

1. **ServiceMonitor label matching** - How Prometheus discovers targets
2. **Service → ServiceMonitor → Prometheus chain** - Each link must be correct
3. **Port naming conventions** - Why port names matter more than numbers
4. **Metrics pipeline debugging** - Systematic approach from app → Prometheus → Grafana
5. **Production observability patterns** - HA, cardinality management, graceful degradation

## Advanced Exercises

1. **Implement metric relabeling** to drop high-cardinality labels
2. **Add PodMonitor** for scraping pods directly (bypass Service)
3. **Configure Prometheus sharding** for horizontal scaling
4. **Set up Thanos** for long-term metric storage
5. **Implement custom Prometheus rules** for derived metrics
6. **Create AlertManager routes** by team/severity
7. **Build custom Grafana dashboard** with variable templating

## References

- [Prometheus Operator Documentation](https://prometheus-operator.dev/)
- [ServiceMonitor CRD Spec](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api.md#servicemonitor)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Kubernetes Monitoring Best Practices](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/)

## Clean Up

```bash
# Delete kind cluster
kind delete cluster --name observability-debug

# Or just remove deployments
kubectl delete -f k8s/base/applications/
kubectl delete -f k8s/overlays/broken/
helm uninstall kube-prometheus -n monitoring
```

## License

MIT License - Educational purposes

## Support

For issues or questions:
1. Run diagnostics script for automated troubleshooting
2. Check Prometheus targets UI for scrape status
3. Review Prometheus logs: `kubectl logs -n monitoring prometheus-kube-prometheus-0`
4. Verify ServiceMonitor → Service → Pod label chain
