# Kubernetes FinOps Platform

Production-ready cost optimization and monitoring system for Kubernetes clusters.

## Architecture Overview

This platform demonstrates enterprise-grade FinOps patterns:

- **Cost Attribution**: Per-namespace, per-team cost allocation with labels
- **Resource Optimization**: VPA for automatic right-sizing, HPA for demand-based scaling
- **Real-time Monitoring**: Prometheus + Grafana stack with custom cost metrics
- **Waste Detection**: Identifies over-provisioned resources and optimization opportunities
- **Multi-tenancy**: ResourceQuotas and LimitRanges for cost governance

### System Components

1. **Log Ingest Service** (Python FastAPI)
   - Cost-optimized async I/O processing
   - Custom Prometheus metrics for cost-per-log tracking
   - Resource-efficient design (512Mi memory for 1000+ concurrent connections)

2. **Cost Analyzer Service** (Python FastAPI)
   - Real-time cost calculation based on resource usage
   - Cloud pricing integration (AWS/GCP/Azure)
   - Waste detection and optimization recommendations

3. **Cost Dashboard** (React + Material-UI)
   - Real-time cost visualization
   - Namespace-level cost breakdown
   - Optimization opportunity alerts

4. **Monitoring Stack**
   - Prometheus for metrics collection
   - Grafana for dashboards
   - Custom recording rules for cost calculations

## Quick Start

### Prerequisites

- Docker
- kubectl
- kind (for local cluster)
- Helm 3.x

### Setup Local Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a 4-node kind cluster with:
- 1 control plane
- 3 worker nodes
- Metrics-server installed
- VPA components deployed

### Build and Deploy

```bash
# Build all Docker images
./scripts/build.sh

# Deploy the platform
./scripts/deploy.sh

# Verify deployment
kubectl get pods -A
```

### Access the Dashboard

```bash
# Port forward to the frontend
kubectl port-forward -n prod-logging svc/cost-dashboard-service 3000:80

# Open browser to http://localhost:3000
```

### Generate Load for Testing

```bash
./scripts/load-test.sh
```

This sends 1000 test log entries to generate cost data for analysis.

## Architecture Deep Dive

### Cost Calculation Model

The platform calculates costs using:

```
pod_cost = (cpu_requests * cpu_hourly_rate) + (memory_requests_gi * memory_hourly_rate)
```

Default rates:
- CPU: $0.048 per vCPU-hour
- Memory: $0.006 per GB-hour

### Resource Quotas

Three-tier namespace structure:

| Namespace | CPU Quota | Memory Quota | Purpose |
|-----------|-----------|--------------|---------|
| prod-logging | 20 cores | 40Gi | Production workloads |
| staging-logging | 5 cores | 10Gi | Staging environment |
| dev-logging | 2 cores | 4Gi | Development testing |

### Autoscaling Strategy

**Horizontal Pod Autoscaler (HPA)**:
- Scales based on CPU (70% target) and memory (80% target)
- Min replicas: 3, Max replicas: 10
- Scale-down stabilization: 5 minutes
- Scale-up: Immediate with max 100% increase

**Vertical Pod Autoscaler (VPA)**:
- Automatic mode for continuous right-sizing
- Min: 100m CPU / 256Mi memory
- Max: 2000m CPU / 2Gi memory
- Recommendation engine analyzes 8 days of historical data

### Monitoring and Alerting

**Prometheus Recording Rules**:
```promql
# Namespace CPU cost per hour
namespace:cpu_cost:hourly = 
  sum by (namespace) (kube_pod_container_resource_requests{resource="cpu"}) * 0.048

# Waste percentage
namespace:waste_percentage = 
  (requests - actual_usage) / requests * 100
```

**Alerts**:
- High waste (>30% for 6+ hours)
- Cost spike (2x daily average)
- Quota exhaustion warnings

## Production Considerations

### Scaling to Production

1. **Multi-cluster Setup**:
   - Deploy monitoring to separate cluster
   - Use Prometheus federation for global view
   - Centralize cost data with Thanos

2. **Security**:
   - Enable RBAC for namespace isolation
   - Use NetworkPolicies for traffic control
   - Implement PodSecurityPolicies

3. **High Availability**:
   - Run monitoring stack in HA mode
   - Configure PodDisruptionBudgets
   - Multi-zone node distribution

4. **Cost Optimization**:
   - Use spot/preemptible instances for non-critical workloads
   - Implement cluster autoscaler for node-level optimization
   - Schedule batch jobs during off-peak hours

### Real-World Examples

This platform implements patterns from:

- **Netflix**: Cost attribution by team/service with chargeback
- **Spotify**: Bin-packing optimization using actual usage data
- **Airbnb**: Automated cost anomaly detection and alerting

### Troubleshooting

**VPA not updating pods**:
```bash
kubectl logs -n kube-system deployment/vpa-recommender
kubectl describe vpa -n prod-logging
```

**HPA not scaling**:
```bash
kubectl get hpa -n prod-logging
kubectl describe hpa log-ingest-hpa -n prod-logging
# Check metrics-server: kubectl top nodes
```

**High costs despite low usage**:
- Check resource requests vs actual usage in Grafana
- Review VPA recommendations for right-sizing
- Identify pods with large request/usage gaps

## Cost Impact

Expected savings with this platform:

- **30-50% infrastructure cost reduction** through right-sizing
- **Eliminate waste** from over-provisioned resources
- **Prevent cost overruns** with quota enforcement
- **Data-driven decisions** with real-time cost visibility

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For questions or issues, contact platform-engineering@example.com
