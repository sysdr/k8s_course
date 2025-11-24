# Kubernetes Resource Management - Log Processing Platform

Production-grade log processing system demonstrating advanced Kubernetes resource management patterns.

## Architecture

### Three-Tier Microservices
- **Log Ingest API** (Guaranteed QoS): Customer-facing service with strict resource guarantees
- **Log Parser** (Burstable QoS): CPU-intensive parsing with HorizontalPodAutoscaler
- **Analytics Engine** (Burstable QoS): Memory-heavy analytics with VerticalPodAutoscaler

### Resource Allocation Strategy

**Guaranteed QoS (Log Ingest)**
```yaml
resources:
  requests.cpu: 1000m
  limits.cpu: 1000m
  requests.memory: 1Gi
  limits.memory: 1Gi
```
Provides absolute scheduling guarantees. Last to be evicted under pressure.

**Burstable QoS (Parser & Analytics)**
```yaml
resources:
  requests.cpu: 500m
  limits.cpu: 2000m  # 4x burst capacity
```
Efficient bin packing with burst capacity for traffic spikes.

### Autoscaling
- **HPA** on Log Parser: Scales replicas 3-20 based on CPU (70%) and memory (80%)
- **VPA** on Analytics Engine: Right-sizes container resources based on actual usage
- **PodDisruptionBudgets**: Ensures 75% availability during node maintenance

### Capacity Management
- **ResourceQuota**: 50 CPU / 100Gi memory namespace limit
- **LimitRange**: Max 8 CPU / 16Gi per pod

## Quick Start

### Prerequisites
- Docker Desktop with Kubernetes enabled, OR
- kind/minikube for local cluster
- kubectl configured

### Build and Deploy

```bash
# Build Docker images
./scripts/build.sh

# Setup local cluster (if using kind)
./scripts/setup-cluster.sh

# Deploy application
./scripts/deploy.sh

# Run load test
./scripts/load-test.sh
```

### Access Services

```bash
# Frontend dashboard
kubectl port-forward -n log-platform svc/frontend 8080:80
# Open http://localhost:8080

# Log Ingest API
kubectl port-forward -n log-platform svc/log-ingest 8000:8000

# Prometheus
kubectl port-forward -n log-platform svc/prometheus 9090:9090

# Grafana (check pod logs for initial admin password)
kubectl port-forward -n log-platform svc/grafana 3000:3000
```

## Testing Resource Management

### Monitor Resource Usage
```bash
# Pod CPU/memory usage
kubectl top pods -n log-platform

# HPA status
kubectl get hpa -n log-platform
kubectl describe hpa log-parser-hpa -n log-platform

# VPA recommendations
kubectl describe vpa analytics-engine-vpa -n log-platform

# Resource quota usage
kubectl describe resourcequota -n log-platform
```

### Simulate Load
```bash
# Generate 1000 log entries
./scripts/load-test.sh

# Watch HPA scale up
watch kubectl get hpa -n log-platform
```

### Trigger OOMKill
```bash
# Reduce memory limits to trigger OOM
kubectl set resources deployment/log-parser -n log-platform \
  --limits=memory=256Mi

# Send high load
./scripts/load-test.sh

# Observe pod restarts
kubectl get pods -n log-platform -w
```

## Architecture Decisions

### Why These Resource Allocations?

**Log Ingest (1 CPU / 1Gi - Guaranteed)**
- Customer-facing API requires absolute stability
- Requests == Limits ensures scheduling guarantees
- PDB maintains 75% availability during updates
- No autoscaling - stable 3 replicas for predictable capacity

**Log Parser (500m-2000m CPU - Burstable + HPA)**
- CPU-intensive regex parsing benefits from burst capacity
- 4x limit allows handling traffic spikes without throttling
- HPA scales replicas under sustained load
- Memory tightly limited (1.5x) to catch leaks early

**Analytics Engine (1-4 CPU, 2-4Gi - Burstable + VPA)**
- Memory-heavy aggregations have variable working sets
- VPA right-sizes based on actual usage patterns
- High CPU limits enable complex query bursts
- Wider memory range (2x) accommodates data growth

### QoS Class Selection

| Service | QoS | Eviction Priority | Rationale |
|---------|-----|-------------------|-----------|
| Log Ingest | Guaranteed | Last | Business-critical API |
| Parser | Burstable | Medium | Stateless, replaceable |
| Analytics | Burstable | Medium | Stateless, can reconstruct |
| Redis | (no limits) | First | Development only |

### Namespace Quotas

Total quota: 50 CPU / 100Gi memory
- Prevents runaway autoscaling
- Forces capacity planning conversations
- Current steady-state: ~15 CPU / 30Gi (30% utilization)
- Peak capacity: ~40 CPU / 70Gi (80% utilization)
- 20% safety margin before hitting quota

## Production Patterns

### Netflix Approach
- Tag services: critical (Guaranteed), standard (Burstable), batch (BestEffort)
- Maintain 40% cluster headroom for zone failures
- VPA recommendations applied during maintenance windows
- Resource usage dashboards drive optimization

### Spotify Model
- Self-service resource allocation with namespace quotas
- Teams learn through experience (OOMKills vs over-provisioning)
- Cluster-wide transparency creates optimization pressure
- 65-70% average utilization with p99 latency within SLOs

## Troubleshooting

### Pods Stuck in Pending
```bash
# Check resource availability
kubectl describe pod <pod-name> -n log-platform
# Look for: "Insufficient cpu" or "Insufficient memory"

# Check namespace quota
kubectl describe resourcequota -n log-platform
```

### CPU Throttling
```bash
# Check throttling metrics
kubectl top pods -n log-platform

# Increase CPU limits
kubectl set resources deployment/log-parser -n log-platform \
  --limits=cpu=4000m
```

### OOMKilled Pods
```bash
# View pod events
kubectl describe pod <pod-name> -n log-platform

# Check actual memory usage
kubectl top pod <pod-name> -n log-platform

# Use VPA recommendations
kubectl describe vpa analytics-engine-vpa -n log-platform
```

## Cleanup

```bash
./scripts/cleanup.sh
```

## Key Learnings

1. **Requests guarantee scheduling** - Set based on minimum required resources
2. **Limits prevent runaway consumption** - Set 1.5-2x requests for CPU, 1.2-1.5x for memory
3. **QoS classes determine eviction order** - Use Guaranteed only for critical services
4. **HPA scales replicas, VPA scales resources** - Use both strategically
5. **ResourceQuotas prevent cluster-wide resource exhaustion** - Essential for multi-tenancy
6. **CPU throttling can occur even with idle capacity** - Set high limits or omit for burst workloads
7. **PodDisruptionBudgets ensure availability** - Especially during node maintenance

## Next Steps

- Add persistent storage with PersistentVolumes
- Implement multi-cluster resource federation
- Add cost optimization with node autoscaling
- Implement resource quotas per team
- Add capacity planning automation
