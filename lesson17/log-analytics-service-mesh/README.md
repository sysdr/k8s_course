# Log Analytics Platform with Istio Service Mesh

A production-grade, multi-tenant log analytics platform demonstrating Kubernetes orchestration patterns with Istio service mesh. This system processes 5,000+ log events per second with comprehensive observability, security, and reliability features.

## Architecture Overview

```
External Traffic
      ↓
  Istio Gateway (mTLS)
      ↓
  Ingestion API (FastAPI) → Kafka → Processing Service
      ↓                                    ↓
  Redis Cache                        TimescaleDB
                                           ↓
                                      Query API
                                           ↓
                                    React Dashboard
```

### Service Mesh Features

- **Automatic mTLS**: All pod-to-pod communication encrypted without code changes
- **Traffic Management**: Intelligent routing, retries, circuit breaking
- **Observability**: Distributed tracing with Jaeger, metrics with Prometheus
- **Security**: Zero-trust network policies, authorization policies

## Prerequisites

- Docker 20.10+
- Kubernetes 1.28+ (kind/minikube for local)
- kubectl 1.28+
- Helm 3.12+
- istioctl 1.20+

## Quick Start

### 1. Setup Local Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a kind cluster with 3 nodes configured for Istio.

### 2. Install Istio Service Mesh

```bash
./scripts/install-istio.sh
```

Installs Istio with demo profile and observability addons (Kiali, Prometheus, Grafana, Jaeger).

### 3. Build Docker Images

```bash
./scripts/build.sh
```

Builds all microservice images and loads them into the kind cluster.

### 4. Deploy Application

```bash
./scripts/deploy.sh
```

Deploys the complete application stack with Kubernetes manifests and Istio configurations.

### 5. Setup Monitoring

```bash
./scripts/monitoring-setup.sh
```

Deploys Prometheus ServiceMonitors and Grafana dashboards.

### 6. Access the Application

```bash
# Dashboard
open http://localhost

# Kiali (Service Mesh Dashboard)
istioctl dashboard kiali

# Grafana (Metrics)
istioctl dashboard grafana

# Jaeger (Distributed Tracing)
istioctl dashboard jaeger
```

### 7. Run Load Tests

```bash
./scripts/load-test.sh
```

## System Components

### Microservices

1. **Ingestion API** (FastAPI)
   - Accepts log events via REST API
   - Publishes to Kafka for asynchronous processing
   - Redis caching for ingestion statistics
   - Exports Prometheus metrics

2. **Processing Service** (Python)
   - Kafka consumer for log events
   - Enriches and stores in TimescaleDB
   - Updates Redis cache for real-time statistics
   - Background worker pattern

3. **Query API** (FastAPI)
   - REST API for querying logs
   - Aggregation and statistics endpoints
   - Direct TimescaleDB queries with connection pooling

4. **Dashboard** (React + TypeScript)
   - Real-time log visualization
   - Statistics and metrics display
   - Material-UI components

### Infrastructure

- **Kafka**: Event streaming backbone
- **TimescaleDB**: Time-series optimized PostgreSQL for log storage
- **Redis**: Caching layer for statistics
- **Istio**: Service mesh for traffic management and security

## Kubernetes Patterns

### High Availability

- **HorizontalPodAutoscaler**: Auto-scales based on CPU/memory
- **PodDisruptionBudget**: Ensures minimum replicas during disruptions
- **Multi-replica deployments**: 3x ingestion-api, 2x query-api

### Security

- **NetworkPolicies**: Restrict pod-to-pod communication
- **RBAC**: Service accounts with minimal permissions
- **Secrets**: Database credentials stored securely
- **mTLS**: Istio enforces encrypted service mesh traffic

### Observability

- **Prometheus**: Service metrics collection
- **Grafana**: Metric visualization
- **Jaeger**: Distributed tracing
- **Kiali**: Service mesh topology

## Istio Configuration

### Traffic Management

**VirtualServices**: Define routing rules with retries and timeouts

```yaml
retries:
  attempts: 3
  perTryTimeout: 10s
  retryOn: 5xx,reset,connect-failure
```

**DestinationRules**: Configure load balancing and circuit breaking

```yaml
outlierDetection:
  consecutiveErrors: 5
  baseEjectionTime: 30s
```

### Security

**PeerAuthentication**: Enforce strict mTLS

```yaml
mtls:
  mode: STRICT
```

**AuthorizationPolicies**: Control service-to-service access

## Performance Characteristics

- **Ingestion throughput**: 5,000+ events/second
- **Query latency**: P95 < 200ms
- **Processing latency**: < 100ms per event
- **Storage**: TimescaleDB handles 100M+ events efficiently

## Development

### Local Development

1. Start individual services:

```bash
cd services/ingestion-api
pip install -r requirements.txt
uvicorn main:app --reload
```

2. Run with Docker Compose:

```bash
docker-compose up
```

### Testing

```bash
# Unit tests
pytest services/*/tests

# Load testing with Locust
cd load-tests
pip install -r requirements.txt
locust -f locustfile.py --host http://localhost
```

## Monitoring & Debugging

### View Service Mesh Topology

```bash
istioctl dashboard kiali
```

Navigate to Graph → Select log-analytics namespace → Enable "Traffic Animation"

### View Distributed Traces

```bash
istioctl dashboard jaeger
```

Search for traces by service name to see request flow across microservices.

### Check Istio Configuration

```bash
# Verify sidecar injection
kubectl get pods -n log-analytics -o jsonpath='{.items[*].spec.containers[*].name}'

# Check proxy status
istioctl proxy-status

# Analyze configuration
istioctl analyze -n log-analytics
```

### Common Issues

**Pods not starting**: Check sidecar injection is enabled

```bash
kubectl label namespace log-analytics istio-injection=enabled
```

**503 errors**: Verify VirtualService and DestinationRule configuration

```bash
kubectl get virtualservices -n log-analytics
kubectl get destinationrules -n log-analytics
```

**High latency**: Check Envoy proxy metrics

```bash
kubectl exec -n log-analytics <pod-name> -c istio-proxy -- pilot-agent request GET stats
```

## Production Considerations

### Scaling

- Horizontal: HPA scales to 10 pods per service
- Vertical: Resource limits prevent noisy neighbor issues
- Database: TimescaleDB sharding for multi-tenant isolation

### Security

- Use cert-manager for automatic TLS certificate management
- Enable Istio strict mTLS mode in production
- Rotate database credentials regularly
- Implement pod security policies

### Monitoring

- Set up AlertManager rules for critical metrics
- Configure PagerDuty/Slack integration
- Monitor Envoy proxy resource usage
- Track service mesh control plane health

## Cleanup

```bash
./scripts/cleanup.sh
```

Deletes the entire kind cluster and all resources.

## Architecture Decisions

### Why Service Mesh?

- **Uniform security**: mTLS without modifying application code
- **Consistent observability**: Automatic tracing and metrics across all services
- **Traffic management**: Retries, timeouts, circuit breaking at infrastructure level
- **Zero-trust networking**: Explicit authorization policies

### Why TimescaleDB?

- Time-series optimized for log data
- PostgreSQL compatibility (familiar tooling)
- Automatic partitioning and compression
- Efficient time-based queries

### Why Kafka?

- Decouples ingestion from processing
- Handles backpressure during traffic spikes
- Provides replay capability for reprocessing
- Industry-standard for event streaming

## Learning Outcomes

After completing this lesson, you'll understand:

1. How service mesh transforms microservice communication
2. Istio architecture (control plane vs data plane)
3. Production Kubernetes patterns (HPA, PDB, NetworkPolicies)
4. Distributed tracing and observability
5. Zero-trust security with mTLS and authorization policies
6. Traffic management patterns (retries, circuit breaking)

## References

- [Istio Documentation](https://istio.io/latest/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Prometheus Operator](https://prometheus-operator.dev/)

---

**Next Lesson**: Lesson 18 - Istio Traffic Management (progressive canary deployments, A/B testing)
