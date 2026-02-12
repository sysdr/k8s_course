# Monitoring Queries Guide

## Prometheus Queries

Access Prometheus at: http://localhost:9090

### Basic Queries

1. **Check if analytics-api is up:**
   ```
   up{job="analytics-api"}
   ```

2. **Python GC Collections:**
   ```
   python_gc_collections_total
   ```

3. **Process Memory Usage:**
   ```
   process_resident_memory_bytes
   process_virtual_memory_bytes
   ```

4. **Process CPU Usage:**
   ```
   process_cpu_seconds_total
   ```

5. **Open File Descriptors:**
   ```
   process_open_fds
   ```

6. **All metrics from analytics-api:**
   ```
   {job="analytics-api"}
   ```

### Advanced Queries

1. **Memory usage in MB:**
   ```
   process_resident_memory_bytes / 1024 / 1024
   ```

2. **Rate of CPU usage:**
   ```
   rate(process_cpu_seconds_total[5m])
   ```

3. **GC collections per second:**
   ```
   rate(python_gc_collections_total[5m])
   ```

## Grafana Queries

Access Grafana at: http://localhost:3000 (admin/admin)

### Data Source
- Prometheus data source is automatically configured at: `http://prometheus:9090`

### Example Queries in Grafana

1. **Memory Usage Panel:**
   - Query: `process_resident_memory_bytes`
   - Format: Time series
   - Unit: bytes (or MB)

2. **CPU Usage Panel:**
   - Query: `rate(process_cpu_seconds_total[5m])`
   - Format: Time series
   - Unit: percent

3. **GC Collections Panel:**
   - Query: `python_gc_collections_total`
   - Format: Time series
   - Legend: `Generation {{generation}}`

4. **Service Status:**
   - Query: `up{job="analytics-api"}`
   - Format: Stat
   - Value: Current

## Troubleshooting

### If queries return empty:

1. **Check Prometheus targets:**
   - Go to: http://localhost:9090/targets
   - Verify that `analytics-api` target is "UP"

2. **Check if metrics endpoint is accessible:**
   ```bash
   kubectl exec -n log-platform <analytics-api-pod> -- wget -qO- http://localhost:8002/metrics
   ```

3. **Verify Prometheus config:**
   ```bash
   kubectl get configmap prometheus-config -n log-platform -o yaml
   ```

4. **Check Grafana data source:**
   - Login to Grafana
   - Go to Configuration > Data Sources
   - Verify Prometheus data source is configured and tested successfully

5. **Restart services if needed:**
   ```bash
   kubectl rollout restart deployment/prometheus -n log-platform
   kubectl rollout restart deployment/grafana -n log-platform
   ```

## Quick Test Queries

Try these in Prometheus to verify everything is working:

```promql
# Service status
up

# All Python metrics
{__name__=~"python_.*"}

# All process metrics
{__name__=~"process_.*"}

# Memory in MB
process_resident_memory_bytes / 1024 / 1024
```
