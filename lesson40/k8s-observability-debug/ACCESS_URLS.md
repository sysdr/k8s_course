# Access URLs and Port-Forward Commands
## Observability Stack - Complete Access Guide

---

## 🔗 Quick Access URLs

### Prerequisites
All services are accessed via `kubectl port-forward`. Run these commands in separate terminals or as background processes.

---

## 📊 Monitoring Stack

### 1. Grafana Dashboard
**Service:** `kube-prometheus-grafana`  
**Namespace:** `monitoring`  
**Port:** 80 → 3000

**Port-Forward Command:**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
```

**Access URL:**
- **Local:** http://localhost:3000
- **Login Username:** `admin`
- **Login Password:** `admin`

**Get Password (if changed):**
```bash
kubectl get secret --namespace monitoring kube-prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode && echo
```

---

### 2. Prometheus UI
**Service:** `kube-prometheus-kube-prome-prometheus`  
**Namespace:** `monitoring`  
**Port:** 9090 → 9090

**Port-Forward Command:**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
```

**Access URL:**
- **Local:** http://localhost:9090

**Key Endpoints:**
- **Targets:** http://localhost:9090/targets
- **Graph:** http://localhost:9090/graph
- **Alerts:** http://localhost:9090/alerts
- **Status:** http://localhost:9090/status
- **API:** http://localhost:9090/api/v1/targets

---

### 3. Alertmanager UI
**Service:** `kube-prometheus-kube-prome-alertmanager`  
**Namespace:** `monitoring`  
**Port:** 9093 → 9093

**Port-Forward Command:**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
```

**Access URL:**
- **Local:** http://localhost:9093

---

## 🚀 Application Services

### 4. Log Processor API
**Service:** `log-processor`  
**Namespace:** `default`  
**Port:** 80 → 8000

**Port-Forward Command:**
```bash
kubectl port-forward svc/log-processor 8000:80
```

**Access URL:**
- **Local:** http://localhost:8000

**API Endpoints:**
- **Health Check:** http://localhost:8000/health
- **Readiness Check:** http://localhost:8000/ready
- **Root/Info:** http://localhost:8000/
- **Ingest Logs:** http://localhost:8000/logs/ingest (POST)
- **Stats:** http://localhost:8000/logs/stats
- **Metrics:** http://localhost:8000/metrics

**Example API Calls:**
```bash
# Health check
curl http://localhost:8000/health

# Ingest a log entry
curl -X POST http://localhost:8000/logs/ingest \
  -H "Content-Type: application/json" \
  -d '{"level":"INFO","message":"Test log","source":"api"}'

# Get statistics
curl http://localhost:8000/logs/stats

# View Prometheus metrics
curl http://localhost:8000/metrics
```

---

### 5. Metrics Exporter
**Service:** `metrics-exporter`  
**Namespace:** `default`  
**Port:** 8081 → 8081

**Port-Forward Command:**
```bash
kubectl port-forward svc/metrics-exporter 8081:8081
```

**Access URL:**
- **Local:** http://localhost:8081

**Endpoints:**
- **Metrics:** http://localhost:8081/metrics

---

### 6. Frontend Dashboard (if deployed)
**Service:** `observability-dashboard` (if created)  
**Namespace:** `default`  
**Port:** 80 → 8080

**Port-Forward Command:**
```bash
kubectl port-forward svc/observability-dashboard 8080:80
```

**Access URL:**
- **Local:** http://localhost:8080

---

## 🔧 Kubernetes API Access

### 7. Kubernetes Dashboard (if installed)
```bash
kubectl proxy
```
**Access URL:**
- **Local:** http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

---

## 📝 All Port-Forward Commands (One-Liners)

Run all port-forwards in background:

```bash
# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &

# Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 &

# Alertmanager
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093 &

# Log Processor API
kubectl port-forward svc/log-processor 8000:80 &

# Metrics Exporter
kubectl port-forward svc/metrics-exporter 8081:8081 &
```

**Stop all port-forwards:**
```bash
pkill -f "kubectl port-forward"
```

---

## 🌐 Service URLs (Cluster-Internal)

These URLs work from within the Kubernetes cluster:

### Prometheus
- **Service URL:** http://kube-prometheus-kube-prome-prometheus.monitoring.svc.cluster.local:9090
- **Operated Service:** http://prometheus-operated.monitoring.svc.cluster.local:9090

### Grafana
- **Service URL:** http://kube-prometheus-grafana.monitoring.svc.cluster.local:80

### Log Processor
- **Service URL:** http://log-processor.default.svc.cluster.local:80
- **Metrics Endpoint:** http://log-processor.default.svc.cluster.local:8080/metrics

### Metrics Exporter
- **Service URL:** http://metrics-exporter.default.svc.cluster.local:8081/metrics

---

## 🔍 Diagnostic URLs

### Prometheus API Queries
```bash
# Query log entries processed
curl "http://localhost:9090/api/v1/query?query=log_entries_processed_total"

# Query request duration
curl "http://localhost:9090/api/v1/query?query=http_request_duration_seconds"

# Get all targets
curl "http://localhost:9090/api/v1/targets"

# Query rate
curl "http://localhost:9090/api/v1/query?query=rate(log_entries_processed_total[1m])"
```

### Grafana API
```bash
# List datasources
curl -u admin:admin http://localhost:3000/api/datasources

# List dashboards
curl -u admin:admin http://localhost:3000/api/dashboards

# Health check
curl http://localhost:3000/api/health
```

---

## 📊 Port Summary

| Service | Local Port | Cluster Port | Protocol |
|---------|------------|--------------|----------|
| Grafana | 3000 | 80 | HTTP |
| Prometheus | 9090 | 9090 | HTTP |
| Alertmanager | 9093 | 9093 | HTTP |
| Log Processor API | 8000 | 80 | HTTP |
| Log Processor Metrics | 8000 | 8080 | HTTP |
| Metrics Exporter | 8081 | 8081 | HTTP |
| Frontend Dashboard | 8080 | 80 | HTTP |

---

## 🚀 Quick Start Script

Create a script to start all port-forwards:

```bash
#!/bin/bash
# start-port-forwards.sh

echo "Starting port-forwards for observability stack..."

kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &
echo "✅ Grafana: http://localhost:3000"

kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 &
echo "✅ Prometheus: http://localhost:9090"

kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093 &
echo "✅ Alertmanager: http://localhost:9093"

kubectl port-forward svc/log-processor 8000:80 &
echo "✅ Log Processor: http://localhost:8000"

kubectl port-forward svc/metrics-exporter 8081:8081 &
echo "✅ Metrics Exporter: http://localhost:8081"

echo ""
echo "All port-forwards started!"
echo "Access Grafana at: http://localhost:3000 (admin/admin)"
echo ""
echo "To stop all port-forwards, run: pkill -f 'kubectl port-forward'"
```

---

## 🔐 Authentication

### Grafana
- **Default Username:** `admin`
- **Default Password:** `admin`
- **Change on first login:** Recommended

### Prometheus
- **No authentication** by default (local cluster)
- **Production:** Enable authentication via ingress/istio

### Alertmanager
- **No authentication** by default (local cluster)

---

## 📱 Mobile/Remote Access

If you need to access from other devices on the same network:

1. **Find your host IP:**
   ```bash
   hostname -I | awk '{print $1}'
   ```

2. **Use host IP instead of localhost:**
   - Grafana: http://YOUR_IP:3000
   - Prometheus: http://YOUR_IP:9090
   - Log Processor: http://YOUR_IP:8000

3. **Ensure firewall allows these ports**

---

## 🐛 Troubleshooting

### Port Already in Use
If a port is already in use, change the local port:
```bash
kubectl port-forward svc/log-processor 8001:80  # Use 8001 instead of 8000
```

### Connection Refused
1. Check if port-forward is running: `ps aux | grep port-forward`
2. Verify service exists: `kubectl get svc -A`
3. Check pod status: `kubectl get pods -A`

### Service Not Found
```bash
# List all services
kubectl get svc -A

# Describe service
kubectl describe svc <service-name> -n <namespace>
```

---

## 📚 Additional Resources

- **Prometheus Query Examples:** See `docs/troubleshooting/common-issues.md`
- **Grafana Dashboard:** Import from `monitoring/grafana/dashboards/`
- **API Documentation:** See application README files

---

*Last Updated: 2026-02-11*
