# Production Kubernetes Log Processing Platform

## 🎯 Overview

Enterprise-grade distributed log processing system built with Kubernetes, demonstrating production-ready patterns for microservices orchestration, service mesh integration, and comprehensive observability.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Istio Ingress Gateway                        │
│                    (mTLS + Load Balancing)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼──────┐ ┌───▼──────┐
        │              │ │          │ │          │
        │ Log          │ │ Log      │ │Analytics │
        │ Ingestion    │ │Processor │ │   API    │
        │              │ │          │ │          │
        │ (HPA: 3-10)  │ │(Replicas)│ │  (VPA)   │
        └──────┬───────┘ └────┬─────┘ └────┬─────┘
               │              │            │
         ┌─────▼──────────────▼────────────▼─────┐
         │                                        │
         │      Kafka + Redis (StatefulSet)      │
         │                                        │
         └────────────────────────────────────────┘
                              │
         ┌────────────────────▼────────────────────┐
         │  Prometheus + Grafana + Jaeger          │
         │  (Full Observability Stack)             │
         └─────────────────────────────────────────┘
```

## 🏗️ Architecture Patterns

### Kubernetes Patterns Implemented

1. **Horizontal Pod Autoscaling (HPA)**
   - Dynamic scaling based on CPU/memory metrics
   - Custom metrics from Prometheus
   - Scale range: 3-10 replicas

2. **Vertical Pod Autoscaling (VPA)**
   - Automatic resource request/limit optimization
   - 7-day learning period
   - In-place updates for non-critical services

3. **Pod Disruption Budgets (PDB)**
   - Ensures minimum availability during disruptions
   - minAvailable: 2 for critical services
   - Protects against voluntary disruptions

4. **Network Policies**
   - Zero-trust networking model
   - Explicit allow-list for pod communication
   - Namespace isolation

5. **Service Mesh (Istio)**
   - Mutual TLS encryption
   - Circuit breaking and retry policies
   - Distributed tracing integration
   - Traffic routing and canary deployments

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Kubernetes 1.28+ (kind/minikube/GKE/EKS)
- kubectl 1.28+
- Helm 3.12+
- 4GB RAM minimum

### Local Development Setup

```bash
# 1. Build all container images
./scripts/build.sh

# 2. Create local Kubernetes cluster
./scripts/setup-cluster.sh

# 3. Deploy the platform
cd scripts && ./deploy.sh

# 4. Setup monitoring
./monitoring-setup.sh

# 5. Run load tests
./load-test.sh
```

### Access the Platform

```bash
# Frontend Dashboard
kubectl port-forward -n log-platform svc/frontend 8080:80
# Visit: http://localhost:8080

# Grafana Monitoring
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Visit: http://localhost:3000 (admin/admin)

# Jaeger Tracing
kubectl port-forward -n monitoring svc/jaeger 16686:16686
# Visit: http://localhost:16686

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit: http://localhost:9090
```

## 📦 Services

### Log Ingestion Service (Python/FastAPI)
- High-throughput HTTP API (10K+ RPS)
- Async Kafka producer integration
- Redis caching for recent logs
- Prometheus metrics export
- Comprehensive health checks

**Endpoints:**
- `POST /api/v1/logs` - Single log ingestion
- `POST /api/v1/logs/batch` - Batch ingestion (up to 1000)
- `GET /health` - Health check
- `GET /ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

### Log Processor Service (Python/FastAPI)
- Kafka stream processing
- Real-time anomaly detection
- Pattern extraction and enrichment
- Metrics aggregation in Redis

### Analytics API (Python/FastAPI)
- Query aggregated metrics
- Recent logs retrieval
- Time-series analytics
- CORS-enabled for frontend

### Frontend (React/TypeScript)
- Real-time dashboard
- Material-UI components
- WebSocket integration
- Responsive design

## 🔧 Configuration

### Environment Variables

**Log Ingestion:**
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
REDIS_HOST=redis
REDIS_PORT=6379
KAFKA_TOPIC=raw-logs
```

**Log Processor:**
```bash
INPUT_TOPIC=raw-logs
OUTPUT_TOPIC=processed-logs
```

### Helm Chart Deployment

```bash
helm install log-platform ./helm/log-platform \
  --namespace log-platform \
  --create-namespace \
  --set replicaCount.ingestion=5 \
  --set autoscaling.enabled=true
```

## 📊 Monitoring & Observability

### Metrics (Prometheus)

- `log_ingestion_total` - Total logs ingested by level/source
- `log_processing_duration_seconds` - Processing latency
- `kafka_publish_errors_total` - Kafka publish failures
- `logs_processed_total` - Successfully processed logs
- `anomalies_detected_total` - Detected anomalies

### Dashboards (Grafana)

1. **Kubernetes Cluster Overview**
   - Pod CPU/Memory usage
   - Network traffic
   - Pod restarts and failures

2. **Log Platform Metrics**
   - Ingestion rate by source
   - Error rate trends
   - Processing latency percentiles
   - Anomaly detection

3. **Istio Service Mesh**
   - Request success rates
   - Latency histograms
   - Circuit breaker status

### Distributed Tracing (Jaeger)

- End-to-end request tracing
- Service dependency visualization
- Latency analysis by span

## 🧪 Testing

### Unit Tests
```bash
cd services/log-ingestion
pytest tests/
```

### Integration Tests
```bash
./scripts/integration-test.sh
```

### Load Testing (Locust)
```bash
cd tests/load
locust -f locustfile.py --host=http://localhost:8000
```

**Load Test Scenarios:**
- Sustained 1000 RPS for 10 minutes
- Burst traffic: 5000 RPS for 30 seconds
- Mixed workload: 70% single logs, 30% batch

## 🔒 Security

### Implemented Security Measures

1. **Network Policies**: Restrict pod-to-pod communication
2. **RBAC**: Principle of least privilege
3. **Service Mesh mTLS**: Encrypted service communication
4. **Secret Management**: Kubernetes Secrets for sensitive data
5. **Non-root Containers**: All services run as user 1000
6. **Image Scanning**: Container vulnerability scanning in CI
7. **Pod Security Standards**: Enforced restricted policy

## 🎓 Kubernetes Patterns Explained

### HPA Strategy
```yaml
# Scale based on CPU and memory
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

**Why 70% CPU threshold?**
- Leaves headroom for traffic spikes
- Prevents thrashing (rapid scale up/down)
- Balances cost vs performance

### VPA vs HPA
- **Use HPA**: For stateless services with horizontal scalability
- **Use VPA**: For stateful services or resource optimization
- **Never both**: On same resource (conflicts)

### Pod Disruption Budgets
```yaml
minAvailable: 2
```
- Ensures 2 pods always running during:
  - Node drains
  - Cluster upgrades
  - Voluntary evictions

## 🏢 Production Deployment

### Cloud Provider Setup

**GKE (Google Kubernetes Engine):**
```bash
gcloud container clusters create log-platform \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --enable-autoscaling \
  --min-nodes=3 \
  --max-nodes=10
```

**EKS (Amazon Elastic Kubernetes Service):**
```bash
eksctl create cluster \
  --name log-platform \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10
```

### Multi-Region Strategy

1. **Active-Active**: Deploy to multiple regions simultaneously
2. **Global Load Balancing**: Route traffic based on geo-location
3. **Data Replication**: Sync Kafka topics across regions
4. **Disaster Recovery**: Automated failover within 60 seconds

## 📈 Capacity Planning

### Resource Requirements (Per Service)

| Service | CPU (Request) | Memory (Request) | Replicas | Total CPU | Total Memory |
|---------|---------------|------------------|----------|-----------|--------------|
| Ingestion | 200m | 256Mi | 3-10 | 0.6-2.0 | 768Mi-2.5Gi |
| Processor | 300m | 512Mi | 2 | 0.6 | 1Gi |
| Analytics | 100m | 128Mi | 2 | 0.2 | 256Mi |
| Frontend | 50m | 64Mi | 2 | 0.1 | 128Mi |

**Cluster Sizing:**
- Development: 2 nodes, 2 vCPU, 4GB RAM each
- Staging: 3 nodes, 4 vCPU, 8GB RAM each
- Production: 5+ nodes, 8 vCPU, 16GB RAM each

## 🐛 Troubleshooting

### Common Issues

**Pods in CrashLoopBackOff:**
```bash
kubectl logs -n log-platform <pod-name> --previous
kubectl describe pod -n log-platform <pod-name>
```

**Service not reachable:**
```bash
# Check endpoints
kubectl get endpoints -n log-platform

# Test service DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup log-ingestion.log-platform.svc.cluster.local
```

**HPA not scaling:**
```bash
# Check metrics availability
kubectl get hpa -n log-platform
kubectl top pods -n log-platform

# Verify metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
```

## 🧹 Cleanup

```bash
# Delete all resources
./scripts/cleanup.sh

# Or manually:
kubectl delete namespace log-platform
kubectl delete namespace monitoring
kind delete cluster --name log-platform
```

## 📚 Learning Resources

### Kubernetes Concepts
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Vertical Pod Autoscaling](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)
- [Pod Disruption Budgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

### Service Mesh
- [Istio Documentation](https://istio.io/latest/docs/)
- [Mutual TLS](https://istio.io/latest/docs/concepts/security/)

### Observability
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Jaeger Tracing](https://www.jaegertracing.io/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with Kubernetes orchestration patterns from FAANG companies
- Inspired by production systems at Netflix, Spotify, and Airbnb
- Service mesh patterns from Istio community best practices

---

**Built for Lesson 43: Advanced Automation** - The Kubernetes Odyssey Course
