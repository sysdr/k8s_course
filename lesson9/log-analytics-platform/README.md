# Log Analytics Platform - Kubernetes Services & Networking

Production-grade distributed log analytics system demonstrating Kubernetes service discovery, networking patterns, and cloud-native microservices architecture.

## Architecture Overview

This system implements a complete log processing pipeline with four microservices:

- **API Gateway** (3 replicas): Central routing layer with ClusterIP, NodePort, and LoadBalancer services
- **Log Ingestion** (5 replicas): High-throughput entry point for log data with HPA (5-20 replicas)
- **Log Processor** (3 replicas): Analyzes and enriches logs with anomaly detection
- **Query Service** (2 replicas): Provides search and filtering capabilities
- **React Frontend** (2 replicas): Real-time dashboard for log visualization

### Service Types Demonstrated

1. **ClusterIP Services**: Internal microservice communication via DNS
   - `log-ingestion.log-analytics.svc.cluster.local`
   - `log-processor.log-analytics.svc.cluster.local`
   - `query-service.log-analytics.svc.cluster.local`

2. **NodePort Services**: Development and debugging access
   - API Gateway: `http://localhost:30080`
   - Frontend: `http://localhost:30081`

3. **LoadBalancer Service**: Production external access with cloud integration
   - API Gateway LoadBalancer with session affinity

### Networking Features

- **Service Discovery**: Zero-configuration DNS-based service routing
- **Network Policies**: Least-privilege pod-to-pod communication rules
- **Istio Service Mesh**: mTLS encryption, traffic management, observability
- **Connection Pooling**: Optimized HTTP/2 connection management
- **Circuit Breaking**: Automatic failure detection and isolation
- **Load Balancing**: Round-robin, least-connection, and weighted algorithms

## Prerequisites

- Docker Desktop or Docker Engine
- kind (Kubernetes in Docker): https://kind.sigs.k8s.io/docs/user/quick-start/
- kubectl: https://kubernetes.io/docs/tasks/tools/
- Minimum 8GB RAM available for Docker

## Quick Start

### 1. Setup Local Kubernetes Cluster

```bash
cd log-analytics-platform
./scripts/setup-cluster.sh
```

This creates a 3-node kind cluster with:
- 1 control plane node
- 2 worker nodes
- Exposed NodePorts (30080, 30081)
- Metrics server for HPA

### 2. Build Docker Images

```bash
./scripts/build.sh
```

Builds all microservices and loads them into kind cluster:
- api-gateway:latest
- log-ingestion:latest
- log-processor:latest
- query-service:latest
- frontend:latest

### 3. Deploy to Kubernetes

```bash
./scripts/deploy.sh
```

Deploys complete system including:
- All microservices with Deployments
- ClusterIP, NodePort, and LoadBalancer Services
- HorizontalPodAutoscalers
- PodDisruptionBudgets
- NetworkPolicies

### 4. Access the Application

**Frontend Dashboard:**
```bash
open http://localhost:30081
```

**API Gateway:**
```bash
curl http://localhost:30080/health
```

**Ingest Test Log:**
```bash
curl -X POST http://localhost:30080/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "test-service",
    "message": "Test log message"
  }'
```

**Query Logs:**
```bash
curl -X POST http://localhost:30080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "service": "test-service",
    "level": "INFO",
    "limit": 10
  }'
```

### 5. Monitor the System

**Watch pods scale:**
```bash
kubectl get pods -n log-analytics -w
```

**Check service endpoints:**
```bash
kubectl get svc -n log-analytics
kubectl get endpoints -n log-analytics
```

**View HPA status:**
```bash
kubectl get hpa -n log-analytics
```

**Check network policies:**
```bash
kubectl get networkpolicies -n log-analytics
kubectl describe networkpolicy api-gateway-policy -n log-analytics
```

## Testing and Validation

### Service Discovery Test

Verify internal DNS resolution:
```bash
kubectl run -n log-analytics -it --rm debug --image=busybox --restart=Never -- sh

# Inside the pod:
nslookup log-ingestion
nslookup log-processor.log-analytics.svc.cluster.local
wget -O- http://api-gateway:8080/health
```

### Load Testing

Generate realistic load to test autoscaling:
```bash
./scripts/load-test.sh http://localhost:30080 60 100
```

Parameters:
- URL: API Gateway endpoint
- Duration: 60 seconds
- Rate: 100 requests/second

Watch pods scale up:
```bash
kubectl get hpa -n log-analytics -w
```

### Network Policy Validation

Test network isolation:
```bash
# This should succeed (API Gateway -> Log Ingestion)
kubectl exec -n log-analytics deployment/api-gateway -- \
  curl -s http://log-ingestion:8080/health

# This should fail (Frontend -> Log Processor blocked by NetworkPolicy)
kubectl exec -n log-analytics deployment/frontend -- \
  curl -s http://log-processor:8080/health
```

### Service Type Testing

**ClusterIP (internal only):**
```bash
kubectl get svc log-ingestion -n log-analytics
# TYPE: ClusterIP, accessible only within cluster
```

**NodePort (external access on nodes):**
```bash
kubectl get svc api-gateway-nodeport -n log-analytics
# TYPE: NodePort, accessible at http://node-ip:30080
```

**LoadBalancer (cloud external IP):**
```bash
kubectl get svc api-gateway-lb -n log-analytics
# TYPE: LoadBalancer, gets external IP from cloud provider
# In kind, this will show <pending> (requires MetalLB for local testing)
```

## Architecture Deep Dive

### Service Discovery Flow

1. **DNS Resolution**: CoreDNS resolves service names to ClusterIP
   - Short name: `log-processor` (same namespace)
   - FQDN: `log-processor.log-analytics.svc.cluster.local`

2. **Load Balancing**: kube-proxy creates iptables/IPVS rules
   - Distributes traffic across healthy pod endpoints
   - Automatic endpoint updates on pod changes

3. **Health Checking**: Readiness probes control service endpoint membership
   - Only ready pods receive traffic
   - Failed pods automatically removed

### Network Policy Architecture

Zero-trust security model:
- Default deny all traffic
- Explicit allow rules for required communication
- DNS access to kube-system namespace
- Prevent lateral movement attacks

### Horizontal Pod Autoscaling

**API Gateway HPA:**
- Min: 3 replicas, Max: 10 replicas
- Target: 70% CPU, 80% memory
- Scale up: 100% increase every 30s
- Scale down: 50% decrease every 300s (stabilization)

**Log Ingestion HPA:**
- Min: 5 replicas, Max: 20 replicas
- Target: 75% CPU
- Handles traffic spikes from 1k to 50k req/s

### Pod Disruption Budgets

Ensure high availability during:
- Node maintenance
- Cluster upgrades
- Voluntary disruptions

Minimum available:
- API Gateway: 2 pods
- Log Ingestion: 3 pods
- Log Processor: 2 pods

## Production Considerations

### Resource Management

Each service has requests and limits:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**Cluster capacity planning:**
- Minimum: 4 CPU cores, 8GB RAM
- Recommended: 8 CPU cores, 16GB RAM
- Production: 32+ CPU cores, 64GB+ RAM

### Security Best Practices

1. **Network Policies**: Enforce least-privilege communication
2. **Service Accounts**: Dedicated SA per microservice
3. **RBAC**: Minimal permissions for service operations
4. **Non-root containers**: All services run as user 1000
5. **Istio mTLS**: Encrypted pod-to-pod communication

### Monitoring and Observability

**Prometheus Metrics:**
- Request rate, error rate, latency (RED method)
- Resource utilization (CPU, memory, network)
- Custom application metrics

**Grafana Dashboards:**
- Service-level indicators (SLIs)
- Kubernetes cluster health
- Application performance metrics

**Distributed Tracing:**
- Request flow through microservices
- Latency breakdown by service
- Error propagation analysis

### Failure Scenarios

**Pod failure:**
- Service automatically removes unhealthy endpoints
- HPA creates replacement pods
- Zero impact to users (with sufficient replicas)

**Node failure:**
- Pods rescheduled to healthy nodes
- Service continues routing to available pods
- PDB ensures minimum availability

**Network partition:**
- NetworkPolicies limit blast radius
- Circuit breakers prevent cascade failures
- Graceful degradation patterns

## Helm Deployment (Alternative)

Deploy using Helm for production:

```bash
helm install log-analytics helm/log-analytics/ \
  --namespace log-analytics \
  --create-namespace \
  --values helm/log-analytics/values.yaml
```

Customize values:
```bash
helm install log-analytics helm/log-analytics/ \
  --set apiGateway.replicaCount=5 \
  --set logIngestion.autoscaling.maxReplicas=30 \
  --set istio.enabled=true
```

## Troubleshooting

### Pods not starting

```bash
kubectl get pods -n log-analytics
kubectl describe pod <pod-name> -n log-analytics
kubectl logs <pod-name> -n log-analytics
```

Common issues:
- ImagePullBackOff: Run `./scripts/build.sh` to load images
- CrashLoopBackOff: Check logs for application errors
- Pending: Check node resources with `kubectl describe nodes`

### Service not accessible

```bash
kubectl get svc -n log-analytics
kubectl get endpoints -n log-analytics
```

Check:
- Service selector matches pod labels
- Pods are in Ready state
- NetworkPolicies allow traffic

### DNS resolution failing

```bash
kubectl run -n log-analytics -it --rm debug --image=nicolaka/netshoot --restart=Never -- bash
nslookup log-ingestion
```

Verify CoreDNS:
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

### HPA not scaling

```bash
kubectl get hpa -n log-analytics
kubectl describe hpa api-gateway-hpa -n log-analytics
```

Requirements:
- Metrics server running: `kubectl get deployment metrics-server -n kube-system`
- Resource requests defined in pod spec
- Sufficient cluster capacity

## Cleanup

Remove all resources:
```bash
./scripts/cleanup.sh
```

This will:
1. Delete log-analytics namespace and all resources
2. Optionally delete kind cluster

## Next Steps

After mastering this lesson, you'll be ready for:

- **Lesson 10**: Break-It-Friday debugging exercises
- **Advanced networking**: Ingress controllers, service mesh patterns
- **Multi-cluster**: Cross-cluster service discovery
- **Production hardening**: Security policies, compliance, cost optimization

## Key Takeaways

1. **Service abstraction**: Stable networking over ephemeral pods
2. **Service types**: ClusterIP for internal, NodePort for dev, LoadBalancer for production
3. **Zero-configuration discovery**: DNS-based service routing
4. **Network isolation**: NetworkPolicies for security
5. **Production patterns**: HPA, PDB, resource management, observability

## Additional Resources

- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Network Policies Guide](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Istio Service Mesh](https://istio.io/latest/docs/)
- [HPA Walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/)
