# Kubernetes Log Processing System

## Production-Grade Pod Patterns Implementation

This project demonstrates advanced Kubernetes pod patterns through a complete distributed log processing system. Built for **Lesson 7: Pods - The Atomic Unit** of the Kubernetes Odyssey course.

## 🎯 What You'll Learn

- **Init Containers**: Database migrations before main app starts
- **Sidecar Pattern**: Nginx serving React static files  
- **Multi-Container Pods**: Shared volumes and network namespace
- **Health Probes**: Liveness vs readiness probe patterns
- **Resource Management**: Requests, limits, and QoS classes
- **High Availability**: HPA, PDB, and pod anti-affinity
- **Production Operations**: Graceful shutdown, rolling updates, monitoring

## 🏗️ Architecture

### System Components

**Microservices:**
- **Ingestion API** (FastAPI): HTTP endpoint for log ingestion → Redis streams
- **Analytics Engine** (Python): Stream consumer → PostgreSQL aggregation
- **Dashboard** (React/TypeScript): Real-time visualization with WebSocket

**Infrastructure:**
- **Redis**: Stream-based message queue
- **PostgreSQL**: Time-series metrics storage (StatefulSet)
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Dashboard visualization

### Key Pod Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                     Ingestion API Pod                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Container (single-container pod)              │ │
│  │  • Health probes: /healthz (liveness) + /ready        │ │
│  │  • Resource limits: 256Mi-512Mi, 250m-500m CPU        │ │
│  │  • Horizontal scaling: HPA (3-10 replicas)            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Analytics Engine Pod                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Init Container: db-migration                          │ │
│  │  • Runs SQL migrations before main app                │ │
│  │  • Different image from main container                │ │
│  │  • Writes to EmptyDir shared with main                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Python Container (main)                               │ │
│  │  • Consumes Redis streams                             │ │
│  │  • Aggregates to PostgreSQL                           │ │
│  │  • PVC mount: /data (10Gi)                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Dashboard Pod                          │
│  ┌────────────────┐  ┌────────────────────────────────────┐ │
│  │ React Build    │  │  Nginx Sidecar                     │ │
│  │ Container      │  │  • Serves static files from React  │ │
│  │ (init phase)   │  │  • TLS termination                 │ │
│  │                │  │  • Reverse proxy to API            │ │
│  └────────────────┘  └────────────────────────────────────┘ │
│         Shared network namespace (localhost)                 │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop or similar (with Kubernetes enabled)
- kubectl CLI
- kind (for local cluster) or access to Kubernetes cluster
- Python 3.11+ (for load testing)

### Option 1: Local Deployment (kind)

```bash
# 1. Build Docker images
./scripts/build.sh

# 2. Create local cluster and load images
./scripts/setup-cluster.sh

# 3. Deploy the system
./scripts/deploy.sh

# 4. Access the dashboard
kubectl port-forward svc/dashboard-service 8080:80 -n log-processing
# Visit http://localhost:8080

# 5. Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n log-processing
# Visit http://localhost:3000 (admin/admin)
```

### Option 2: Helm Deployment

```bash
# Install via Helm
helm install log-processing ./helm/log-processing \
  --namespace log-processing \
  --create-namespace

# Check status
helm status log-processing -n log-processing

# Upgrade
helm upgrade log-processing ./helm/log-processing -n log-processing
```

### Option 3: Kustomize

```bash
# Development overlay
kubectl apply -k k8s/overlays/dev

# Production overlay
kubectl apply -k k8s/overlays/prod
```

## 📊 Monitoring & Observability

### Prometheus Metrics

Access Prometheus:
```bash
kubectl port-forward svc/prometheus 9090:9090 -n log-processing
```

Key metrics exposed:
- `log_ingestion_total` (counter) - Total logs ingested by level
- `log_ingestion_duration_seconds` (histogram) - Ingestion latency
- `logs_processed_total` (counter) - Logs processed by analytics engine
- `processing_errors_total` (counter) - Processing failures
- `active_streams` (gauge) - Active Redis stream consumers

### Grafana Dashboards

Pre-configured dashboards for:
- Pod resource utilization (CPU, memory)
- Application metrics (throughput, latency)
- Kubernetes cluster health
- HPA scaling events

### Health Checks

```bash
# Check ingestion API health
kubectl exec -n log-processing deployment/ingestion-api -- \
  curl -s localhost:8000/healthz

# Check readiness
kubectl exec -n log-processing deployment/ingestion-api -- \
  curl -s localhost:8000/ready
```

## 🧪 Testing

### Manual API Test

```bash
# Port forward to ingestion service
kubectl port-forward svc/ingestion-service 8000:8000 -n log-processing

# Send a test log
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "service": "test-service",
    "message": "Test log from Kubernetes pod!"
  }'
```

### Load Testing

```bash
# Run load test (60 seconds at 100 RPS)
./scripts/load-test.sh 60 100

# Monitor HPA scaling
watch kubectl get hpa -n log-processing

# Monitor pod count
watch kubectl get pods -n log-processing
```

### Integration Tests

```bash
# Run integration test suite
python3 tests/integration/test_end_to_end.py
```

## 🔧 Operational Tasks

### Scaling

```bash
# Manual scaling
kubectl scale deployment ingestion-api --replicas=5 -n log-processing

# HPA automatically scales based on:
# - CPU utilization (target: 70%)
# - Memory utilization (target: 80%)

# Check HPA status
kubectl get hpa -n log-processing
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/ingestion-api \
  ingestion-api=ingestion-api:v2 \
  -n log-processing

# Watch rollout
kubectl rollout status deployment/ingestion-api -n log-processing

# Rollback if needed
kubectl rollout undo deployment/ingestion-api -n log-processing
```

### Debugging Pods

```bash
# Check pod status
kubectl get pods -n log-processing

# View logs
kubectl logs -f deployment/ingestion-api -n log-processing

# For init containers
kubectl logs pod/analytics-engine-xxx -c db-migration -n log-processing

# Describe pod for events
kubectl describe pod/ingestion-api-xxx -n log-processing

# Shell into pod
kubectl exec -it deployment/ingestion-api -n log-processing -- /bin/sh
```

### Pod Failure Scenarios

Test pod resilience:

```bash
# Delete pod (will be recreated)
kubectl delete pod -l app=ingestion-api -n log-processing

# Simulate node failure
kubectl drain <node-name> --ignore-daemonsets

# Verify PDB prevents disruption
kubectl get pdb -n log-processing
```

## 📚 Pod Pattern Deep Dive

### 1. Init Containers Pattern

The analytics engine uses an init container for database migrations:

**Benefits:**
- Migrations run before app starts (fail-fast if DB incompatible)
- Different image/tools without bloating main container
- Sequential execution guarantees order
- Shared EmptyDir for state passing

**Use cases:**
- Database schema migrations
- Configuration fetching (Vault, ConfigMaps)
- Dependency waiting (service readiness)
- File system preparation

### 2. Sidecar Pattern

The dashboard pod uses nginx as a sidecar:

**Benefits:**
- Separation of concerns (React build vs serving)
- Smaller production images (20MB vs 1.2GB)
- TLS termination without app code changes
- Shared localhost network namespace

**Use cases:**
- Service mesh proxies (Envoy, Linkerd)
- Log shippers (Fluent Bit, Filebeat)
- Security proxies (OAuth2 Proxy)
- Monitoring agents (StatsD, OpenTelemetry)

### 3. Resource Management

Every pod specifies requests and limits:

**Strategy:**
- **Requests**: P95 actual usage (scheduling guarantee)
- **Limits**: 2x requests (headroom for spikes)
- **CPU**: Throttling is graceful (set limits higher)
- **Memory**: OOM kills are disruptive (set limits conservatively)

**QoS Classes:**
- Guaranteed: requests = limits (highest priority)
- Burstable: requests < limits (medium priority)
- BestEffort: no requests/limits (lowest priority)

### 4. Health Probes

**Liveness Probe:**
- Checks if application is running
- Failures trigger container restart
- Use for: deadlock detection, unrecoverable errors
- Example: `/healthz` endpoint

**Readiness Probe:**
- Checks if application can serve traffic
- Failures remove pod from service endpoints
- Use for: dependency checks (DB connection), warm-up periods
- Example: `/ready` endpoint

**Startup Probe:**
- Allows slow-starting containers time to start
- Disables liveness checks until passing
- Use for: applications with long initialization

## 🏭 Production Considerations

### High Availability

- **HPA**: Automatically scales 3-10 replicas based on CPU/memory
- **PDB**: Ensures minimum 2 replicas during node drains
- **Anti-Affinity**: Spreads pods across nodes/zones
- **Resource Requests**: Guarantees scheduling capacity

### Security

- **Non-root containers**: All pods run as user 1000
- **Read-only root filesystem**: Prevents container modifications
- **Network Policies**: Restricts pod-to-pod traffic
- **RBAC**: Minimal permissions via ServiceAccount
- **Security contexts**: Drop all capabilities, no privilege escalation

### Observability

- **Structured logging**: JSON format with trace IDs
- **Prometheus metrics**: RED metrics (Rate, Errors, Duration)
- **Distributed tracing**: Jaeger integration (future)
- **Health endpoints**: Standardized `/healthz`, `/ready`, `/metrics`

### Disaster Recovery

- **StatefulSet**: Stable persistent storage for PostgreSQL
- **PVCs**: Data survives pod restarts
- **Backup strategy**: Velero integration (future)
- **Graceful shutdown**: 30s termination grace period

## 🎓 Learning Outcomes

After completing this lesson, you'll understand:

✅ **Why pods are Kubernetes' atomic unit** - not containers
✅ **Shared network namespace** - how containers in a pod communicate via localhost
✅ **Init containers** - bootstrapping patterns and migration strategies
✅ **Sidecar pattern** - separation of concerns in multi-container pods
✅ **Resource requests vs limits** - scheduling contracts and QoS
✅ **Health probe differences** - liveness vs readiness probe use cases
✅ **Pod lifecycle** - restart policies and exponential backoff
✅ **Production patterns** - HPA, PDB, graceful shutdown, monitoring
✅ **Operational debugging** - how to troubleshoot pod failures

## 🔗 Related Lessons

- **Lesson 6**: Intro to Kubernetes (foundation)
- **Lesson 8**: Workload Controllers - Deployments (next)
- **Lesson 9**: Services and Ingress (networking)
- **Lesson 10**: ConfigMaps and Secrets (configuration)

## 🤝 Contributing

This is a learning project for the Kubernetes Odyssey course. Feel free to:
- Report issues or bugs
- Suggest improvements
- Share your learning experience

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

**Pods stuck in Pending:**
```bash
kubectl describe pod <pod-name> -n log-processing
# Check events for scheduling failures (insufficient CPU/memory)
```

**Init container failures:**
```bash
kubectl logs <pod-name> -c db-migration -n log-processing
# Check migration logs for SQL errors
```

**Redis connection failures:**
```bash
kubectl exec deployment/ingestion-api -n log-processing -- \
  nc -zv redis-service 6379
```

**HPA not scaling:**
```bash
kubectl describe hpa -n log-processing
# Ensure metrics-server is installed
# Check if pod metrics are available
kubectl top pods -n log-processing
```

### Debug Commands Cheat Sheet

```bash
# Pod status
kubectl get pods -n log-processing -o wide

# Pod events
kubectl get events -n log-processing --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n log-processing
kubectl top nodes

# Service endpoints
kubectl get endpoints -n log-processing

# Network debugging
kubectl run debug --image=nicolaka/netshoot -it --rm -n log-processing

# Port forward for debugging
kubectl port-forward pod/<pod-name> 8000:8000 -n log-processing
```

## 📖 Additional Resources

- [Kubernetes Pods Documentation](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

**Kubernetes Odyssey - Lesson 7: Pods - The Atomic Unit**

*Master the fundamentals, scale to production.*
