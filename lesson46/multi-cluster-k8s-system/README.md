# Multi-Cluster Kubernetes Log Processing System

Production-ready federated Kubernetes system demonstrating multi-cluster architecture patterns with Karmada orchestration.

## System Architecture

This system implements a distributed log processing pipeline across three geographic regions:
- **US West (us-west-2)**: Primary ingestion cluster
- **EU West (eu-west-1)**: European data residency compliance
- **AP Southeast (ap-southeast-1)**: APAC low-latency serving

### Core Components

- **Log Collector**: FastAPI-based ingestion service with Kafka integration
- **Log Processor**: Async processing pipeline with enrichment logic
- **Analytics Engine**: Real-time log analytics and aggregation
- **Dashboard**: React-based multi-cluster observability interface

### Kubernetes Patterns Demonstrated

1. **Federated Workload Distribution** via Karmada PropagationPolicy
2. **Cross-Cluster Service Mesh** with Istio multi-primary setup
3. **Policy-Driven Placement** using cluster affinity and taints/tolerations
4. **Automatic Failover** with graceful workload evacuation
5. **Unified Observability** across federated infrastructure

## Prerequisites

- Docker 24.0+
- Kind 0.20+ or Minikube 1.30+
- kubectl 1.28+
- Helm 3.12+
- Python 3.11+ (for load testing)

## Quick Start

### 1. Set Up Multi-Cluster Environment

```bash
./scripts/setup-cluster.sh
```

This creates four Kind clusters:
- `control-plane`: Karmada management cluster
- `cluster-us-west`: US region workload cluster
- `cluster-eu-west`: EU region workload cluster
- `cluster-ap-southeast`: APAC region workload cluster

### 2. Build and Deploy Services

```bash
./scripts/deploy.sh
```

Builds container images and deploys via Karmada federation policies.

### 3. Deploy Monitoring Stack

```bash
./scripts/monitoring-setup.sh
```

Installs Prometheus, Grafana, and Jaeger across clusters.

### 4. Verify Deployment

```bash
# Check cluster health
kubectl get clusters --context kind-control-plane

# Verify workload distribution
kubectl get deployments --context kind-cluster-us-west
kubectl get deployments --context kind-cluster-eu-west
kubectl get deployments --context kind-cluster-ap-southeast

# Check Karmada resource bindings
kubectl get resourcebindings --context kind-control-plane
```

## Architecture Deep Dive

### Karmada Federation Model

Karmada uses a hub-spoke topology:
- **Management Cluster**: Runs Karmada control plane, does NOT run workloads
- **Member Clusters**: Register with Karmada, execute federated workloads

**PropagationPolicy** defines workload distribution:
```yaml
placement:
  clusterAffinity:
    clusterNames: [cluster-us-west, cluster-eu-west, cluster-ap-southeast]
  replicaScheduling:
    replicaSchedulingType: Divided
    weightPreference:
      dynamicWeight: AvailableReplicas
```

This distributes replicas based on available cluster capacity, automatically rebalancing on failures.

### Cross-Cluster Networking

Each cluster has isolated Pod CIDRs:
- `cluster-us-west`: 10.244.0.0/16
- `cluster-eu-west`: 10.245.0.0/16
- `cluster-ap-southeast`: 10.246.0.0/16

Istio east-west gateway enables cross-cluster service discovery:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: cross-cluster-gateway
spec:
  selector:
    istio: eastwestgateway
  servers:
  - port:
      number: 15443
      protocol: TLS
    tls:
      mode: AUTO_PASSTHROUGH
    hosts:
    - "*.global"
```

Services use `.global` suffix for multi-cluster routing: `log-collector.global`

### Failure Handling Strategy

**Cluster Failure Detection**:
- Karmada health checker monitors API server availability
- Unhealthy clusters receive taint: `cluster.karmada.io/not-ready`

**Workload Evacuation**:
1. Karmada marks cluster unhealthy
2. ResourceBindings updated to exclude failed cluster
3. Workloads redistribute to healthy clusters
4. PodDisruptionBudgets respected during migration

**Recovery**:
- Cluster health restored → taint removed
- Automatic workload rebalancing based on capacity

### Monitoring and Observability

**Prometheus Federation**:
- Each cluster runs Prometheus instance
- Thanos sidecar uploads metrics to object storage
- Unified Thanos Query provides global view

**Distributed Tracing**:
- Jaeger collectors in each cluster
- Spans shipped to centralized Elasticsearch
- Cross-cluster request tracing enabled

**Key Metrics**:
- `karmada_resource_propagation_duration_seconds`: Policy application latency
- `istio_request_duration_milliseconds{destination_cluster!="source_cluster"}`: Cross-cluster latency
- `kube_pod_info`: Pod distribution across clusters

## Load Testing

Generate realistic multi-cluster load:

```bash
./scripts/load-test.sh
```

This simulates 100 concurrent users sending log batches to random cluster endpoints.

**Expected Behavior**:
- Requests automatically load-balanced across clusters
- Failover demonstrated by stopping one cluster during test
- Cross-cluster latency visible in Jaeger traces

## Scaling Strategies

### Horizontal Scaling

HPA configured per deployment with cross-cluster awareness:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

Karmada redistributes replicas as clusters scale.

### Cluster Addition

Add new geographic region:

```bash
# Create cluster
kind create cluster --name cluster-ap-south

# Join to Karmada
karmadactl join cluster-ap-south --cluster-kubeconfig=$HOME/.kube/config

# Update PropagationPolicy
kubectl edit propagationpolicy multi-cluster-log-system --context kind-control-plane
# Add cluster-ap-south to clusterNames
```

Workloads automatically propagate to new cluster.

## Troubleshooting

### Workload Not Propagating

```bash
# Check cluster registration
kubectl get clusters --context kind-control-plane

# Verify propagation policy
kubectl get propagationpolicy --context kind-control-plane -o yaml

# Check resource bindings
kubectl get resourcebindings --context kind-control-plane
kubectl describe resourcebinding <name> --context kind-control-plane
```

### Cross-Cluster Communication Failing

```bash
# Verify Istio east-west gateway
kubectl get pods -n istio-system --context kind-cluster-us-west

# Test cross-cluster connectivity
kubectl run test-pod --image=curlimages/curl --context kind-cluster-us-west -- \
  curl -v log-collector.global:8000/health

# Check Istio VirtualService
kubectl get virtualservices --all-namespaces --context kind-control-plane
```

### Cluster Unhealthy

```bash
# Check cluster status
kubectl get cluster <cluster-name> --context kind-control-plane -o yaml

# View cluster taints
kubectl get cluster <cluster-name> --context kind-control-plane -o jsonpath='{.spec.taints}'

# Force cluster healthy (emergency)
kubectl patch cluster <cluster-name> --context kind-control-plane \
  --type=json -p='[{"op": "remove", "path": "/spec/taints"}]'
```

## Production Considerations

### Security

- **mTLS**: Istio enforces mutual TLS for all cross-cluster communication
- **RBAC**: ServiceAccounts with least-privilege policies
- **Network Policies**: Restrict pod-to-pod traffic within clusters
- **Secret Management**: Use external secrets operator for production

### Cost Optimization

- **Spot Instances**: 30-50% cost reduction for non-critical workloads
- **Cluster Autoscaling**: Right-size node pools per region
- **Resource Limits**: Prevent resource exhaustion, enable better bin-packing
- **Cross-Region Traffic**: Minimize via intelligent routing

### Disaster Recovery

- **Multi-Region Active-Active**: All clusters serve production traffic
- **Regional Failover**: <30s failover via DNS/Global Load Balancer
- **Data Replication**: Kafka mirroring for stateful workloads
- **Backup**: etcd snapshots + application state to object storage

## Production Deployment

For production, replace Kind with managed Kubernetes:

```bash
# Example: AWS EKS multi-region
eksctl create cluster --name=us-west-2-prod --region=us-west-2 --nodes=5
eksctl create cluster --name=eu-west-1-prod --region=eu-west-1 --nodes=5
eksctl create cluster --name=ap-southeast-1-prod --region=ap-southeast-1 --nodes=3

# Join to Karmada management cluster
karmadactl join us-west-2-prod --cluster-kubeconfig=<kubeconfig>
karmadactl join eu-west-1-prod --cluster-kubeconfig=<kubeconfig>
karmadactl join ap-southeast-1-prod --cluster-kubeconfig=<kubeconfig>
```

Update Helm values for production:
```yaml
logCollector:
  replicaCount: 10
  autoscaling:
    maxReplicas: 100
  
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
```

## Cleanup

Remove all clusters:

```bash
./scripts/cleanup.sh
```

## Further Reading

- [Karmada Documentation](https://karmada.io/docs/)
- [Istio Multi-Cluster](https://istio.io/latest/docs/setup/install/multicluster/)
- [Kubernetes Federation](https://kubernetes.io/docs/concepts/cluster-administration/federation/)
- [Thanos](https://thanos.io/)

## License

MIT
