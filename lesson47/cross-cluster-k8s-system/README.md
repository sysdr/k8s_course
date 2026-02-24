# Cross-Cluster Kubernetes Log Processing System

Production-grade multi-cluster log processing demonstrating cross-cluster networking patterns.

## Architecture

This system implements a distributed log processing pipeline across two Kubernetes clusters:

**Cluster A (Log Ingestion)**:
- FastAPI service receiving logs via HTTP
- Exposed via LoadBalancer for cross-cluster access
- Publishes logs to Kafka
- Caches recent logs in Redis

**Cluster B (Log Processing)**:
- Consumes logs from Kafka
- Aggregates and stores in PostgreSQL
- Queries Cluster A via cross-cluster HTTP calls
- Demonstrates service-to-service communication across cluster boundaries

### Key Patterns Demonstrated

1. **LoadBalancer Service Exposure**: External access to cluster services
2. **Cross-Cluster DNS/IP Discovery**: Services finding each other across clusters
3. **Health-Aware Routing**: Circuit breakers and failover strategies
4. **Comprehensive Monitoring**: Prometheus metrics for cross-cluster observability
5. **Horizontal Scaling**: HPA based on CPU/memory metrics

## Prerequisites

- Docker (20.10+)
- kubectl (1.28+)
- kind (0.20+)
- Python 3.11+ (for load testing)

## Quick Start

### 1. Create Local Clusters

```bash
cd scripts
./setup-cluster.sh
```

This creates two kind clusters with MetalLB for LoadBalancer support.

### 2. Build and Load Docker Images

```bash
./build.sh
```

Builds service images and loads them into both clusters.

### 3. Deploy the System

```bash
./deploy.sh
```

Deploys all services and infrastructure to both clusters.

### 4. Verify Deployment

Check Cluster A:
```bash
kubectl config use-context kind-cluster-a
kubectl get pods -n logging
kubectl get svc log-ingestion-lb -n logging
```

Check Cluster B:
```bash
kubectl config use-context kind-cluster-b
kubectl get pods -n logging
```

## Testing

### Send Test Logs

```bash
# Get LoadBalancer IP
LOADBALANCER_IP=$(kubectl get svc log-ingestion-lb -n logging \
    --context kind-cluster-a -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Send a test log
curl -X POST http://$LOADBALANCER_IP:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "service": "test-service",
    "level": "INFO",
    "message": "Test log message",
    "trace_id": "test-123"
  }'
```

### View Processing Stats

```bash
# Get Cluster B service
kubectl port-forward -n logging svc/log-processor 8001:8000 --context kind-cluster-b

# Query stats
curl http://localhost:8001/stats
```

### Run Load Test

```bash
cd tests/load
pip install aiohttp

# Update CLUSTER_A_URL in load-test.py with LoadBalancer IP
python load-test.py
```

## Monitoring

### Prometheus Metrics

Forward Prometheus:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090 --context kind-cluster-a
```

Access at http://localhost:9090

Key Metrics:
- `log_ingestion_requests_total`: Total ingestion requests
- `logs_processed_total`: Total processed logs
- `cross_cluster_calls_total`: Cross-cluster API calls
- `log_processing_latency_seconds`: Processing latency histogram

### Health Checks

Cluster A:
```bash
curl http://$LOADBALANCER_IP:8000/health
```

Cluster B (demonstrates cross-cluster health check):
```bash
kubectl exec -it -n logging deployment/log-processor -- \
    curl http://localhost:8000/health
```

## Production Considerations

### Security

1. **Network Policies**: Restrict LoadBalancer access to known CIDRs
2. **mTLS**: Implement mutual TLS for cross-cluster communication
3. **Secrets Management**: Use external-secrets-operator or sealed-secrets
4. **RBAC**: Apply least-privilege service accounts

### Scaling

1. **HPA Configuration**: Adjust based on actual load patterns
2. **VPA**: Consider vertical pod autoscaling for resource optimization
3. **Cluster Autoscaling**: Configure cloud provider autoscalers
4. **Multi-Region**: Deploy clusters across regions for geo-distribution

### Reliability

1. **Pod Disruption Budgets**: Ensure minimum replicas during updates
2. **Circuit Breakers**: Implement client-side circuit breakers (Resilience4j)
3. **Retry Logic**: Exponential backoff for failed cross-cluster calls
4. **Fallback Mechanisms**: Local buffering when cross-cluster unavailable

### Observability

1. **Distributed Tracing**: Implement Jaeger/OpenTelemetry
2. **Log Aggregation**: Centralize logs from both clusters
3. **Alerting**: Configure AlertManager for cross-cluster failures
4. **Dashboards**: Create Grafana dashboards for cross-cluster metrics

## Architecture Decisions

### Why LoadBalancer vs Ingress?

LoadBalancer provides Layer 4 connectivity, working with any protocol (gRPC, custom protocols). Ingress is Layer 7 and HTTP-specific. For cross-cluster service communication, LoadBalancer is simpler and more versatile.

### Why Two Clusters?

Models real-world scenarios:
- Regulatory compliance (data sovereignty)
- Blast radius containment
- Geographic distribution
- Environment isolation (dev/staging/prod)

### Why Kafka for Cross-Cluster Communication?

Async messaging decouples clusters. If Cluster B is down, logs buffer in Kafka. Provides natural backpressure and replay capabilities.

## Troubleshooting

### LoadBalancer Pending

```bash
kubectl describe svc log-ingestion-lb -n logging
```

Check MetalLB installation and IP pool configuration.

### Cross-Cluster Connection Failed

1. Verify LoadBalancer IP is accessible from Cluster B
2. Check ConfigMap has correct `cluster_a_url`
3. Review network policies and security groups

### Kafka Connection Issues

```bash
kubectl logs -n logging deployment/log-ingestion
kubectl logs -n logging deployment/log-processor
```

Ensure Kafka and Zookeeper are running and accessible.

## Cleanup

```bash
cd scripts
./cleanup.sh
```

Deletes both kind clusters.

## Next Steps

1. **Implement Istio Multi-Cluster**: For advanced traffic management
2. **Add Karmada**: For centralized multi-cluster orchestration
3. **Configure External DNS**: Automate DNS record creation
4. **Implement GitOps**: Use ArgoCD/Flux for deployment automation
5. **Multi-Region Deployment**: Deploy to cloud provider (EKS, GKE, AKS)

## Resources

- [Kubernetes Multi-Cluster](https://kubernetes.io/docs/concepts/cluster-administration/federation/)
- [Istio Multi-Cluster](https://istio.io/latest/docs/setup/install/multicluster/)
- [LoadBalancer Service](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
- [Cross-Cluster Communication Patterns](https://www.cncf.io/blog/2021/04/12/multi-cluster-kubernetes-challenges-and-patterns/)
