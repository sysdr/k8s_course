# Log Analytics Platform with NGINX Ingress Controller

A production-grade Kubernetes implementation demonstrating advanced Ingress patterns for multi-tenant log analytics.

## 🏗️ Architecture

This system demonstrates:

- **NGINX Ingress Controller** as the single entry point for all traffic
- **Path-based routing** directing different API endpoints to specific services
- **Rate limiting** protecting services from abuse
- **Horizontal Pod Autoscaling** for dynamic capacity management
- **Complete observability** with Prometheus and Grafana

### Components

1. **Log Ingestion Service** (FastAPI) - Receives and stores logs
2. **Query Service** (FastAPI) - Searches and retrieves logs
3. **Analytics Service** (FastAPI) - Aggregates and analyzes log data
4. **Frontend Dashboard** (React + TypeScript) - Real-time visualization
5. **NGINX Ingress Controller** - Routes all external traffic
6. **Monitoring Stack** - Prometheus + Grafana for observability

## 🚀 Quick Start

### Prerequisites

- Docker
- Kubernetes cluster (kind, minikube, or cloud provider)
- kubectl configured

### 1. Build Images

```bash
cd log-analytics-platform
./scripts/build.sh
```

### 2. Deploy to Kubernetes

```bash
./scripts/deploy.sh
```

This will:
- Deploy NGINX Ingress Controller with optimized configuration
- Deploy all microservices with HPA enabled
- Configure Ingress resources with rate limiting
- Set up Prometheus and Grafana for monitoring

### 3. Access the Application

For local clusters:
```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Then open: http://localhost:8080

## 📊 Ingress Routes

All traffic flows through the NGINX Ingress Controller:

```
http://localhost:8080/                    → Frontend Dashboard
http://localhost:8080/api/ingest         → Log Ingestion Service
http://localhost:8080/api/query          → Query Service
http://localhost:8080/api/analytics      → Analytics Service
```

## 🔧 Testing the System

### Manual Testing

```bash
# Ingest a log
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "message": "Test log message",
    "source": "test-client"
  }'

# Query logs
curl "http://localhost:8080/api/query?level=INFO&limit=10"

# Get analytics summary
curl http://localhost:8080/api/analytics/summary
```

### Load Testing

```bash
./scripts/load-test.sh http://localhost:8080
```

Generates:
- 50 concurrent log ingestion requests
- 100 concurrent query requests
- 50 concurrent analytics requests

## 📈 Monitoring

### Access Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Open http://localhost:9090

Key metrics to monitor:
- `nginx_ingress_controller_requests` - Request rate by path
- `nginx_ingress_controller_request_duration_seconds` - Latency distribution
- `logs_ingested_total` - Log ingestion rate
- `queries_executed_total` - Query execution rate

### Access Grafana

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

Open http://localhost:3000 (admin/admin)

## 🎯 Key Ingress Patterns Demonstrated

### 1. Path-Based Routing

Different URL paths route to different backend services:
```yaml
- path: /api/ingest
  backend: log-ingestion-service:8000
- path: /api/query
  backend: query-service:8001
- path: /api/analytics
  backend: analytics-service:8002
```

### 2. Rate Limiting

Protects services from abuse:
```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "100"
  nginx.ingress.kubernetes.io/limit-connections: "10"
```

### 3. SSL/TLS Termination

Ingress handles HTTPS, backends use HTTP:
```yaml
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: tls-certificate
```

### 4. CORS Configuration

Enables frontend-backend communication:
```yaml
annotations:
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "*"
```

### 5. Custom Headers

Security headers added at ingress layer:
```yaml
annotations:
  nginx.ingress.kubernetes.io/configuration-snippet: |
    more_set_headers "X-Frame-Options: DENY";
    more_set_headers "X-Content-Type-Options: nosniff";
```

## 🔍 Troubleshooting

### Ingress Controller Not Ready

```bash
kubectl get pods -n ingress-nginx
kubectl describe pod -n ingress-nginx <pod-name>
kubectl logs -n ingress-nginx <pod-name>
```

### 502 Bad Gateway

Usually indicates backend pod not ready:
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Rate Limiting Triggered

Check Ingress logs:
```bash
kubectl logs -n ingress-nginx <ingress-pod> | grep 429
```

### Metrics Not Showing

Verify Prometheus scraping:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets
```

## 🏢 Production Considerations

### For Production Deployment:

1. **Enable SSL/TLS**
   ```bash
   # Install cert-manager
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   
   # Update Ingress annotations
   cert-manager.io/cluster-issuer: "letsencrypt-prod"
   nginx.ingress.kubernetes.io/ssl-redirect: "true"
   ```

2. **Tune Ingress Controller Resources**
   ```yaml
   resources:
     requests:
       cpu: 500m
       memory: 512Mi
     limits:
       cpu: 2000m
       memory: 2Gi
   ```

3. **Configure Persistent Storage**
   - Use persistent volumes for log storage
   - Connect to external databases (PostgreSQL, Elasticsearch)
   - Add Redis for caching

4. **Implement Authentication**
   ```yaml
   nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.default.svc.cluster.local/oauth2/auth"
   ```

5. **Set Up Multi-Region**
   - Deploy ingress controllers in each region
   - Use GeoDNS for routing
   - Configure cross-region replication

## 📝 Helm Deployment

Alternative deployment using Helm:

```bash
cd helm
helm install log-analytics ./log-analytics \
  --set global.domain=your-domain.com \
  --set ingress.tls.enabled=true
```

Customize values:
```bash
helm install log-analytics ./log-analytics -f custom-values.yaml
```

## 🧹 Cleanup

```bash
./scripts/cleanup.sh
```

Removes all Kubernetes resources including:
- NGINX Ingress Controller
- Application deployments and services
- Monitoring stack
- All Ingress resources

## 📚 Learning Outcomes

After completing this lesson, you understand:

1. **How Ingress Controllers work** - Layer 7 routing in Kubernetes
2. **Path-based routing patterns** - Directing traffic to different services
3. **Rate limiting strategies** - Protecting services from overload
4. **SSL/TLS termination** - Managing certificates at the ingress layer
5. **Production ingress patterns** - Used by companies like Netflix, Spotify, Airbnb

## 🔗 Next Steps

- **Lesson 17**: Service Mesh with Istio for service-to-service communication
- Implement canary deployments with weighted traffic splitting
- Add WAF (Web Application Firewall) rules
- Set up multi-cluster ingress with global load balancing

## 📖 References

- [NGINX Ingress Controller Documentation](https://kubernetes.github.io/ingress-nginx/)
- [Kubernetes Ingress Concepts](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [cert-manager for SSL/TLS](https://cert-manager.io/)
- [Prometheus Monitoring](https://prometheus.io/)
