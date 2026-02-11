# Common Observability Stack Issues

## Issue: Grafana Shows "No Data"

### Symptoms
- All dashboard panels display "No data" message
- Queries return empty results
- Datasource connection test passes

### Root Causes

1. **No metrics being scraped**
   - Check Prometheus targets: none active for your service
   - ServiceMonitor not discovered by Prometheus
   - Service/Pod not exposing metrics endpoint

2. **Metrics exist but queries are wrong**
   - Metric name typo in dashboard query
   - Label filters excluding all series
   - Time range doesn't match data retention

3. **Prometheus query timeout**
   - Too many time series in query
   - Long time range with high resolution
   - Prometheus under-resourced

### Debugging Steps

```bash
# 1. Check if Prometheus is scraping targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Visit http://localhost:9090/targets

# 2. List all available metrics
# In Prometheus UI: query: {__name__=~".+"}

# 3. Test specific metric existence
# Query: http_request_duration_seconds

# 4. Check ServiceMonitor
kubectl get servicemonitor -n <namespace> -o yaml

# 5. Verify Service endpoints
kubectl get endpoints <service-name> -n <namespace>

# 6. Test metrics endpoint directly
kubectl run curl --image=curlimages/curl -it --rm -- \
  curl http://<pod-ip>:<port>/metrics
```

### Solutions

**If no targets are being scraped:**
```bash
# Add required label to ServiceMonitor
kubectl label servicemonitor <name> team=platform -n <namespace>

# Verify ServiceMonitor selector matches Service labels
kubectl get service <name> -o jsonpath='{.metadata.labels}'
kubectl get servicemonitor <name> -o jsonpath='{.spec.selector.matchLabels}'
```

**If queries are wrong:**
- Copy query from dashboard
- Test in Prometheus UI directly
- Use "Explore" feature to build query incrementally

**If Prometheus is overloaded:**
```yaml
# Increase Prometheus resources
resources:
  limits:
    cpu: 4000m
    memory: 16Gi
```

## Issue: ServiceMonitor Not Creating Scrape Targets

### Symptoms
- ServiceMonitor exists but Prometheus shows zero targets
- No errors in Prometheus logs
- Service and Pods are healthy

### Root Causes

1. **Label selector mismatch**
   - Prometheus serviceMonitorSelector doesn't match ServiceMonitor labels
   - ServiceMonitor selector doesn't match Service labels

2. **Namespace issues**
   - ServiceMonitor in different namespace than Service
   - Prometheus doesn't have RBAC for target namespace

3. **Port name mismatch**
   - ServiceMonitor references non-existent port name
   - Service port names don't match

### Debugging Steps

```bash
# Check Prometheus serviceMonitorSelector
kubectl get prometheus -n monitoring -o yaml | \
  grep -A 10 serviceMonitorSelector

# Check ServiceMonitor labels
kubectl get servicemonitor -n <namespace> \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels}{"\n"}{end}'

# Check if selectors match
kubectl get service <name> -o yaml | grep -A5 "labels:"
kubectl get servicemonitor <name> -o yaml | grep -A5 "matchLabels:"

# Check Prometheus RBAC
kubectl get clusterrole prometheus -o yaml
```

### Solutions

**Fix label mismatch:**
```yaml
# ServiceMonitor must have label matching Prometheus selector
metadata:
  labels:
    team: platform  # Add this if Prometheus selects team=platform

# ServiceMonitor selector must match Service labels exactly
spec:
  selector:
    matchLabels:
      app: myapp
      component: backend  # Match all Service labels
```

**Fix port reference:**
```yaml
# Service ports
spec:
  ports:
  - name: metrics  # Use descriptive name
    port: 8080
    targetPort: metrics

# ServiceMonitor endpoint
spec:
  endpoints:
  - port: metrics  # Reference by name, not number
```

## Issue: High Cardinality Causing Prometheus OOM

### Symptoms
- Prometheus pod restarting frequently
- OOMKilled in pod status
- Slow query performance
- High memory usage

### Root Causes

- Labels with too many unique values (user_id, request_id, session_id)
- Metrics explosion from dynamic label values
- Inefficient metric design

### Debugging Steps

```bash
# Check cardinality per metric
# In Prometheus UI:
topk(20, count by (__name__)({__name__=~".+"}))

# Check cardinality per job
topk(10, count by (job)({__name__=~".+"}))

# Find high-cardinality labels
# Query a specific metric with all labels
http_requests_total

# Check memory usage
kubectl top pod -n monitoring prometheus-kube-prometheus-0
```

### Solutions

**Drop high-cardinality labels:**
```yaml
# In ServiceMonitor
spec:
  endpoints:
  - port: metrics
    metricRelabelings:
    - sourceLabels: [user_id]
      action: labeldrop
    - sourceLabels: [request_id]
      action: labeldrop
```

**Limit label values:**
```yaml
# Keep only specific label values
metricRelabelings:
- sourceLabels: [status_code]
  regex: '(200|201|400|401|403|404|500|503)'
  action: keep
```

**Aggregate before ingestion:**
```python
# In application code, don't use user_id as label
# BAD:
http_requests.labels(user_id=user_id, endpoint=endpoint).inc()

# GOOD:
http_requests.labels(endpoint=endpoint).inc()
# Store user_id in logs, not metrics
```

## Issue: Metrics Endpoint Returns 404

### Symptoms
- Prometheus target shows "404 Not Found"
- curl to /metrics returns 404
- Other endpoints work fine

### Root Causes

- Metrics endpoint not implemented
- Wrong URL path in ServiceMonitor
- Metrics library not initialized
- Port mismatch

### Solutions

**Verify metrics endpoint:**
```bash
# Test directly on pod
kubectl exec -it <pod-name> -- wget -O- localhost:8080/metrics

# Check what's listening on port
kubectl exec -it <pod-name> -- netstat -tlnp
```

**Fix ServiceMonitor path:**
```yaml
spec:
  endpoints:
  - port: metrics
    path: /metrics  # Verify this matches application route
```

## Issue: Prometheus Storage Full

### Symptoms
- "not enough space" errors in Prometheus logs
- Metrics queries fail
- Old data missing

### Solutions

**Increase retention:**
```yaml
prometheusSpec:
  retention: 30d  # Increase from default 15d
  retentionSize: 50GB
```

**Use PersistentVolume:**
```yaml
storageSpec:
  volumeClaimTemplate:
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd
```

**Implement Thanos for long-term storage:**
- Ship metrics to object storage
- Reduce local retention to 7d
- Query historical data from Thanos
