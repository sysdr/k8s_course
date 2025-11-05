# Production Kubernetes Log Processing Platform

A production-ready, scalable log processing platform built with Kubernetes, demonstrating advanced orchestration patterns including service mesh, autoscaling, and comprehensive observability.

## System Architecture

This platform processes application logs through a microservices architecture:

1. **Log Ingestion Service** (FastAPI): HTTP API for log ingestion with Kafka publishing
2. **Log Processor Workers** (Python): Kafka consumers that enrich and store logs
3. **Analytics Dashboard** (React + TypeScript): Real-time log analytics visualization
4. **Infrastructure**: Kafka, PostgreSQL, Redis
5. **Service Mesh**: Istio for mTLS, traffic management, and observability
6. **Monitoring**: Prometheus, Grafana, Jaeger for full observability

### Key Kubernetes Patterns

- **HorizontalPodAutoscaler**: Dynamic scaling based on CPU/memory metrics
- **VerticalPodAutoscaler**: Automatic resource request optimization
- **PodDisruptionBudgets**: High availability during updates
- **NetworkPolicies**: Zero-trust network security
- **StatefulSets**: Ordered deployment for stateful services (Kafka, PostgreSQL)
- **Istio Service Mesh**: mTLS, circuit breakers, traffic routing

## Prerequisites

- Docker 20.10+
- Kubernetes cluster (kind, minikube, or cloud provider)
- kubectl 1.28+
- Helm 3.12+
- Optional: Istio 1.19+

## Quick Start

### 1. Setup Local Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a local Kubernetes cluster with 3 worker nodes.

### 2. Build Docker Images

```bash
./scripts/build.sh
```

Builds all microservice images.

### 3. Deploy Platform

```bash
./scripts/deploy.sh
```

Deploys all components to Kubernetes.

### 4. Access Services

Forward ports to access services locally:

```bash
# Prometheus
kubectl port-forward -n log-platform svc/prometheus 9090:9090

# Grafana
kubectl port-forward -n log-platform svc/grafana 3000:3000

# Frontend Dashboard
kubectl port-forward -n log-platform svc/frontend 8080:80

# Log Ingestion API
kubectl port-forward -n log-platform svc/log-ingestion 8000:8000
```

## Local Development

### Running Services Locally

Each service can be run independently for development:

```bash
# Log Ingestion Service
cd services/log-ingestion
pip install -r requirements.txt
uvicorn app.main:app --reload

# Log Processor
cd services/log-processor
pip install -r requirements.txt
python -m app.main

# Frontend
cd frontend
npm install
npm start
```

### Docker Compose (Development)

For local development without Kubernetes:

```bash
docker-compose up
```

## Testing

### Unit Tests

```bash
# Python services
cd services/log-ingestion
pytest tests/

cd ../log-processor
pytest tests/

# Frontend
cd frontend
npm test
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
cd load-tests
locust -f locustfile.py --host=http://localhost:8000
```

Or use the provided script:

```bash
./scripts/load-test.sh
```

## Monitoring & Observability

### Prometheus Metrics

- **Log Ingestion**: Request count, latency, Kafka publish success/failure
- **Log Processor**: Messages processed, processing latency, DB write latency, cache hit/miss
- **Kubernetes**: Pod CPU/memory, restart counts, node metrics

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin123):

- Kubernetes Cluster Overview
- Application Metrics
- Service Latency Analysis

### Distributed Tracing

Jaeger UI at http://localhost:16686:

- Request traces across microservices
- Latency breakdown by service
- Error tracking

## Scaling Strategies

### Horizontal Scaling

HPA automatically scales based on metrics:

```bash
# Check HPA status
kubectl get hpa -n log-platform

# Manual scale (for testing)
kubectl scale deployment log-ingestion --replicas=10 -n log-platform
```

### Vertical Scaling

VPA recommendations:

```bash
kubectl describe vpa log-processor-vpa -n log-platform
```

### Load Testing Scenarios

Test autoscaling behavior:

```bash
# Generate load
./scripts/load-test.sh

# Watch scaling
kubectl get hpa -n log-platform -w
```

## Production Deployment

### Multi-Region Strategy

For production, deploy across multiple regions:

1. Regional Kubernetes clusters
2. Global load balancer (AWS Route 53, Cloudflare)
3. Cross-region Kafka replication
4. Database read replicas per region

### Security Hardening

- Enable Pod Security Standards
- Use network policies for zero-trust
- Rotate Secrets regularly
- Enable audit logging
- Use private container registry

### Cost Optimization

- Use VPA to right-size pods
- Enable cluster autoscaling
- Use spot instances for non-critical workloads
- Implement proper resource limits
- Monitor and optimize storage usage

## Troubleshooting

### Common Issues

**Pods stuck in Pending**:
```bash
kubectl describe pod <pod-name> -n log-platform
# Check events for scheduling failures
```

**Service not accessible**:
```bash
kubectl get svc -n log-platform
kubectl get endpoints -n log-platform
# Verify service selectors match pod labels
```

**High memory usage**:
```bash
kubectl top pods -n log-platform
# Check VPA recommendations
kubectl describe vpa -n log-platform
```

### Logs

```bash
# Application logs
kubectl logs -f deployment/log-ingestion -n log-platform

# Previous container logs
kubectl logs deployment/log-processor -n log-platform --previous

# All pods in namespace
kubectl logs -l app=log-processor -n log-platform --tail=100
```

## Architecture Decisions

### Why Kafka?

- Durable message queue with replay capability
- Horizontal scalability with partitioning
- Consumer groups for parallel processing
- Better than Redis Pub/Sub for critical data

### Why PostgreSQL in Kubernetes?

For learning purposes. In production:
- Use managed services (RDS, CloudSQL)
- StatefulSets add operational complexity
- Backup/restore is challenging

### Why Istio?

- mTLS encryption without code changes
- Advanced traffic management (canary, blue-green)
- Observability with distributed tracing
- Circuit breakers and retries

Trade-off: 50-100ms latency overhead and 0.5 CPU per pod for sidecar.

## Performance Benchmarks

### Expected Throughput

- Log Ingestion: 5,000 req/s per pod
- Log Processor: 500 messages/s per pod
- System capacity: 50,000 logs/s with default scaling

### Resource Usage

- Log Ingestion: 500m CPU, 1Gi memory per pod
- Log Processor: 1 CPU, 2Gi memory per pod
- Total cluster: ~40 cores, 80Gi memory for full deployment

## Cleanup

Remove all resources:

```bash
./scripts/cleanup.sh
```

Or manually:

```bash
kubectl delete namespace log-platform
kind delete cluster --name log-platform  # or minikube delete
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Report bugs](https://github.com/your-org/log-platform/issues)
- Documentation: [Full docs](https://docs.example.com)
- Slack: #log-platform channel

## Additional Resources

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for learning production Kubernetes patterns**
