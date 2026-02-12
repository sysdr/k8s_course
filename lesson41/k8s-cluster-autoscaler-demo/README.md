# Kubernetes Cluster Autoscaling Demo - Log Processing Platform

A production-ready microservices system demonstrating Kubernetes cluster autoscaling patterns, built with Python FastAPI backend services and React frontend.

## System Architecture

The system consists of:

- **Log Ingestion Service** (FastAPI): Receives logs via HTTP API, publishes to Kafka
- **Log Processor Service** (Python): Consumes from Kafka, aggregates statistics in Redis
- **Analytics API** (FastAPI): Provides REST API for querying log analytics
- **Frontend Dashboard** (React + Material-UI): Real-time visualization of log data
- **Infrastructure**: Redis (cache), Kafka (message queue), Zookeeper (Kafka coordination)

### Kubernetes Patterns Demonstrated

1. **Horizontal Pod Autoscaling (HPA)**: Automatically scales replicas based on CPU/memory
2. **Pod Disruption Budgets (PDB)**: Ensures minimum replicas during voluntary disruptions
3. **Resource Requests/Limits**: Proper resource allocation for scheduler decisions
4. **Health Checks**: Liveness and readiness probes for pod lifecycle management
5. **Service Mesh (Istio)**: mTLS, traffic management, circuit breakers
6. **Observability**: Prometheus metrics, Grafana dashboards
7. **Manual Cluster Scaling**: Simulating cluster autoscaler behavior in kind

## Prerequisites

- Docker (version 20+)
- kubectl (version 1.28+)
- kind (Kubernetes in Docker) version 0.20+
- Python 3.11+ (for load testing)
- Node.js 18+ (optional, for frontend development)

## Quick Start

### 1. Clone and Setup

```bash
cd k8s-cluster-autoscaler-demo
```

### 2. Create Kubernetes Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a kind cluster with 1 control plane and 2 worker nodes.

### 3. Build Docker Images

```bash
./scripts/build.sh
```

Builds all microservice images and loads them into the kind cluster.

### 4. Deploy Application

```bash
./scripts/deploy.sh
```

Deploys all services, infrastructure components, and autoscaling resources.

### 5. Deploy Monitoring Stack

```bash
./scripts/monitoring-setup.sh
```

Deploys Prometheus and Grafana for observability.

### 6. Access the Application

```bash
# Get frontend service details
kubectl get svc frontend -n log-platform

# If LoadBalancer is pending in kind, use port-forward
kubectl port-forward -n log-platform svc/frontend 8080:80
```

Access the dashboard at http://localhost:8080

## Testing Cluster Autoscaling

### Observe Initial State

```bash
kubectl get nodes
kubectl get pods -n log-platform -o wide
```

You should see 2 worker nodes and pods distributed across them.

### Generate Load to Trigger HPA

```bash
# Install locust for load testing
cd load-tests
pip install -r requirements.txt

# Port forward the ingestion service
kubectl port-forward -n log-platform svc/log-ingestion 8000:8000

# Run load test in another terminal
../scripts/load-test.sh http://localhost:8000 300 200
```

This generates 200 requests/second for 5 minutes.

### Monitor Autoscaling

```bash
# Watch HPA decisions
kubectl get hpa -n log-platform -w

# Watch pod scaling
kubectl get pods -n log-platform -w

# Check resource utilization
kubectl top pods -n log-platform
kubectl top nodes
```

As load increases, HPA will scale replicas up. You'll see pods enter **Pending** state when nodes run out of capacity.

### Simulate Cluster Autoscaler

In production, the cluster autoscaler would provision new nodes automatically. In kind, we simulate this manually:

```bash
# Delete and recreate cluster with 3 nodes
kind delete cluster --name log-platform-cluster
kind create cluster --config infrastructure/kind-config-expanded.yaml

# Redeploy everything
./scripts/build.sh
./scripts/deploy.sh
```

Observe that pending pods now schedule on the new node.

### Monitor with Prometheus/Grafana

```bash
# Port forward Prometheus
kubectl port-forward -n log-platform svc/prometheus 9090:9090

# Port forward Grafana
kubectl port-forward -n log-platform svc/grafana 3000:3000
```

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Production Patterns

### Resource Requests and Limits

Services are configured with appropriate resource requests/limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

The scheduler uses requests for placement decisions. Limits prevent resource overconsumption.

### HPA Behavior Configuration

HPAs include stabilization windows and scaling policies:

```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 60
    policies:
    - type: Percent
      value: 100
      periodSeconds: 60
  scaleDown:
    stabilizationWindowSeconds: 300
```

This prevents thrashing during traffic fluctuations.

### Pod Disruption Budgets

PDBs ensure minimum replicas during node maintenance:

```yaml
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: log-ingestion
```

## Istio Service Mesh (Optional)

To enable Istio features:

```bash
# Install Istio
istioctl install --set profile=demo -y

# Label namespace for sidecar injection
kubectl label namespace log-platform istio-injection=enabled

# Deploy Istio resources
kubectl apply -f k8s/istio/

# Restart pods to inject sidecars
kubectl rollout restart deployment -n log-platform
```

## Architecture Insights

### Why Two-Tier Autoscaling?

**HPA (Pod-level)** responds in 15-30 seconds to CPU/memory changes. It works within existing node capacity.

**Cluster Autoscaler (Node-level)** responds in 2-5 minutes (cloud provider provisioning time). It adds capacity when HPA can't schedule pods.

This hierarchy optimizes for both latency and cost:
- Fast scaling for predictable load (HPA)
- Elastic capacity for unpredictable spikes (cluster autoscaling)

### Resource Request Anti-Pattern

Setting requests too low leads to overcommitment. The scheduler thinks nodes have capacity, but runtime exhausts resources. This causes:
- OOMKilled pods
- CPU throttling
- Failed health checks

Always profile actual resource usage and set requests to P95 values.

### Scale-Down Delays

Aggressive scale-down (< 5 min) causes thrashing during oscillating traffic. Each scale event incurs:
- Pod termination latency
- Connection draining
- Image pulling on new pods

Production systems delay scale-down 10-20 minutes.

## Troubleshooting

### Pods Stuck in Pending

```bash
kubectl describe pod <pod-name> -n log-platform
```

Look for:
- `Insufficient cpu` or `Insufficient memory` → Need more nodes
- `Node affinity/anti-affinity` → Check node labels/taints

### HPA Not Scaling

```bash
kubectl describe hpa -n log-platform
```

Verify:
- Metrics server is running: `kubectl get deployment metrics-server -n kube-system`
- Resource requests are set on pods
- Target metrics are valid

### Service Unreachable

```bash
kubectl get endpoints -n log-platform
```

If endpoints are empty, pods aren't passing readiness probes.

## Cleanup

```bash
./scripts/cleanup.sh
```

Deletes the namespace and kind cluster.

## Next Steps

- Implement VPA (VerticalPodAutoscaler) for right-sizing requests
- Add custom metrics (e.g., Kafka lag) for HPA
- Deploy across multiple node pools (compute-optimized, memory-optimized)
- Implement predictive autoscaling based on traffic patterns
- Add multi-region failover

## References

- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [Istio Traffic Management](https://istio.io/latest/docs/concepts/traffic-management/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Architecture Insight**: Cluster autoscaling isn't about blindly adding nodes—it's about maintaining a resource buffer (typically 10-20% free capacity) that absorbs traffic spikes before HPA completes scaling. The autoscaler then refills that buffer. This "headroom strategy" separates Netflix-level systems from proof-of-concepts.
