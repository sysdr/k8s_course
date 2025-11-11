# Monitoring Guide: Prometheus and Grafana

## Step 1: Deploy Monitoring Stack

First, ensure the monitoring namespace and services are deployed:

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus and Grafana
kubectl apply -f monitoring/

# Verify pods are running
kubectl get pods -n monitoring
```

Wait for both Prometheus and Grafana pods to be in `Running` state.

## Step 2: Access Prometheus

### 2.1 Port Forward Prometheus

In a terminal, run:

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

### 2.2 Open Prometheus UI

1. Open your browser and go to: **http://localhost:9090**
2. You should see the Prometheus web interface

### 2.3 View Metrics in Prometheus

**Query Examples:**

1. **Logs Ingested Total:**
   ```
   logs_ingested_total
   ```

2. **Logs by Level:**
   ```
   sum by (level) (logs_ingested_total)
   ```

3. **HTTP Requests:**
   ```
   http_requests_total
   ```

4. **Request Duration (P95):**
   ```
   histogram_quantile(0.95, http_request_duration_seconds_bucket)
   ```

5. **All Metrics from Log Ingestion API:**
   - Go to **Status → Targets** to see scraped endpoints
   - Go to **Graph** tab to run queries
   - Use the dropdown to browse available metrics

**To verify metrics are being scraped:**
- Go to **Status → Targets** - you should see pods with `prometheus.io/scrape: "true"` annotation
- Go to **Status → Service Discovery** - check Kubernetes pod discovery

## Step 3: Access Grafana

### 3.1 Port Forward Grafana

In a **new terminal** (keep Prometheus port-forward running), run:

```bash
kubectl port-forward -n monitoring svc/grafana 3001:3000
```

### 3.2 Open Grafana UI

1. Open your browser and go to: **http://localhost:3001**
2. Default credentials:
   - **Username:** `admin`
   - **Password:** `admin` (you'll be prompted to change it on first login)

### 3.3 Configure Prometheus Data Source

1. Click on **⚙️ Configuration** (gear icon) → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set the URL to: `http://prometheus.monitoring.svc.cluster.local:9090`
   - Or if using port-forward: `http://localhost:9090`
5. Click **Save & Test** - should show "Data source is working"

### 3.4 Create or Import Dashboard

**Option A: Create a New Dashboard**

1. Click **+** → **Create Dashboard**
2. Click **Add visualization**
3. In the query editor, select your Prometheus data source
4. Enter a query, for example:
   ```
   sum by (level) (logs_ingested_total)
   ```
5. Configure visualization type (Graph, Pie Chart, etc.)
6. Click **Apply**

**Option B: Import Pre-configured Dashboard**

The project includes a dashboard configuration at `monitoring/grafana/dashboards/log-processing.json`. To import:

1. Click **+** → **Import**
2. Upload the JSON file or paste its contents
3. Select your Prometheus data source
4. Click **Import**

**Option C: Use Grafana Explore**

1. Click **Explore** (compass icon) in the left menu
2. Select Prometheus data source
3. Enter queries like:
   - `logs_ingested_total`
   - `sum by (level) (logs_ingested_total)`
   - `rate(http_requests_total[5m])`

## Step 4: View Metrics

### Key Metrics to Monitor

1. **Log Ingestion Metrics:**
   - `logs_ingested_total` - Total logs ingested
   - `logs_ingested_total{level="INFO"}` - INFO level logs
   - `logs_ingested_total{level="ERROR"}` - ERROR level logs

2. **Log Processing Metrics:**
   - `logs_processed_total` - Total logs processed
   - `logs_processed_total{level="ERROR"}` - Error logs processed

3. **HTTP Metrics:**
   - `http_requests_total` - Total HTTP requests
   - `http_request_duration_seconds` - Request duration histogram
   - `http_requests_total{status="200"}` - Successful requests

4. **System Metrics:**
   - `container_cpu_usage_seconds_total` - CPU usage
   - `container_memory_usage_bytes` - Memory usage

### Example Grafana Queries

**Logs Ingested Rate (per minute):**
```
rate(logs_ingested_total[1m]) * 60
```

**Error Rate:**
```
rate(logs_ingested_total{level="ERROR"}[5m])
```

**Request Rate:**
```
rate(http_requests_total[5m])
```

**P95 Latency:**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Step 5: Generate Test Data

To see metrics populate, generate some log data:

```bash
# Port forward the API (if not already done)
kubectl port-forward -n log-processing svc/log-ingestion-api 8080:8000

# In another terminal, send test logs
for i in {1..100}; do
  curl -X POST http://localhost:8080/api/v1/logs \
    -H "Content-Type: application/json" \
    -d "{\"level\":\"INFO\",\"service\":\"test-service\",\"message\":\"Test log $i\"}"
  sleep 0.1
done
```

Then refresh your Prometheus/Grafana dashboards to see the metrics update.

## Troubleshooting

### Prometheus not scraping metrics

1. Check if pods have the annotation:
   ```bash
   kubectl get pods -n log-processing -o jsonpath='{.items[*].metadata.annotations.prometheus\.io/scrape}'
   ```
   Should show `true`

2. Check Prometheus targets:
   - In Prometheus UI: **Status → Targets**
   - Should show pods as "UP"

3. Check Prometheus logs:
   ```bash
   kubectl logs -n monitoring deployment/prometheus
   ```

### Grafana can't connect to Prometheus

1. Verify Prometheus service:
   ```bash
   kubectl get svc -n monitoring prometheus
   ```

2. Test connectivity from Grafana pod:
   ```bash
   kubectl exec -n monitoring deployment/grafana -- wget -qO- http://prometheus.monitoring.svc.cluster.local:9090/api/v1/status/config
   ```

3. If using port-forward, ensure the URL in Grafana is `http://localhost:9090`

### No metrics appearing

1. Ensure the log ingestion API is running and receiving requests
2. Check if metrics endpoint is accessible:
   ```bash
   kubectl port-forward -n log-processing svc/log-ingestion-api 8080:8000
   curl http://localhost:8080/metrics
   ```
   Should show Prometheus-formatted metrics

3. Verify Prometheus is scraping the `/metrics` endpoint:
   - Check pod annotations include `prometheus.io/path: "/metrics"`
   - Check `prometheus.io/port: "8000"`

## Quick Reference

**Port Forwarding Commands:**
```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Grafana  
kubectl port-forward -n monitoring svc/grafana 3001:3000

# API (for testing)
kubectl port-forward -n log-processing svc/log-ingestion-api 8080:8000
```

**URLs:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- API: http://localhost:8080

**Default Grafana Credentials:**
- Username: `admin`
- Password: `admin` (change on first login)

