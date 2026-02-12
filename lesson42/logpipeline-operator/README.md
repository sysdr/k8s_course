# LogPipeline Operator - Production Kubernetes Custom Controller

A production-grade Kubernetes operator implementing the Controller Pattern for declarative log processing pipelines. This system demonstrates advanced Kubernetes concepts including Custom Resource Definitions (CRDs), reconciliation loops, and operator patterns at scale.

## 🏗️ System Architecture

The LogPipeline Operator extends the Kubernetes API to manage complex log processing workflows through custom resources. The system consists of:

### Core Components

1. **Custom Controller (Operator)**
   - Watches LogPipeline custom resources
   - Implements reconciliation loop for desired state management
   - Manages lifecycle of log processing components
   - Handles scaling, updates, and failure recovery

2. **LogPipeline CRD**
   - Defines declarative API for log processing pipelines
   - Supports multiple source types (Kubernetes, syslog, HTTP)
   - Configurable processors (filter, parse, enrich, transform)
   - Multiple sink destinations (Elasticsearch, S3, Kafka)

3. **Microservices Architecture**
   - **Log Collector**: Ingests logs from various sources
   - **Log Processor**: Applies transformations and enrichment
   - **Log Sink**: Writes processed logs to destinations

4. **Infrastructure**
   - Kafka for message streaming and buffering
   - Redis for caching and state management
   - Elasticsearch for log storage and search

5. **Observability Stack**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Custom metrics from operator and services

## 🚀 Quick Start

### Prerequisites

- Docker (20.10+)
- kubectl (1.28+)
- kind (0.20+) or minikube
- Helm 3.12+

### 1. Setup Local Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a multi-node kind cluster configured for the operator.

### 2. Build and Load Images

```bash
./scripts/build.sh
```

Builds all Docker images and loads them into the kind cluster.

### 3. Deploy the System

```bash
./scripts/deploy.sh
```

Deploys:
- Custom Resource Definitions
- Operator with RBAC
- Infrastructure components (Kafka, Redis, Elasticsearch)
- Monitoring stack (Prometheus, Grafana)
- Example LogPipeline resource

### 4. Verify Deployment

```bash
# Check operator status
kubectl get pods -n logging-system

# Check LogPipeline resources
kubectl get logpipelines -n logging

# Check created components
kubectl get deployments -n logging
```

## 📋 Creating LogPipeline Resources

### Basic Example

```yaml
apiVersion: logpipeline.k8s.io/v1
kind: LogPipeline
metadata:
  name: my-pipeline
  namespace: logging
spec:
  source:
    type: kubernetes
    namespaces:
      - production
  processors:
    - type: filter
      config:
        excludeDebug: true
    - type: parse
      config:
        format: json
  sink:
    type: elasticsearch
    config:
      endpoint: "http://elasticsearch:9200"
      index: "logs-production"
```

### Advanced Configuration

```yaml
apiVersion: logpipeline.k8s.io/v1
kind: LogPipeline
metadata:
  name: advanced-pipeline
  namespace: logging
spec:
  source:
    type: kubernetes
    namespaces:
      - production
      - staging
    labelSelector:
      app: backend
      tier: api
  
  collector:
    replicas: 5
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
      limits:
        cpu: "1000m"
        memory: "1Gi"
  
  processors:
    - type: filter
      config:
        excludeDebug: true
        includeErrors: true
    - type: parse
      config:
        format: json
        extractFields: ["requestId", "userId"]
    - type: enrich
      config:
        addNodeInfo: true
        addPodMetadata: true
    - type: transform
      config:
        maskPII: true
  
  processor:
    replicas: 10
  
  sink:
    type: elasticsearch
    replicas: 3
    config:
      endpoint: "http://elasticsearch:9200"
      index: "logs-production"
      batchSize: 1000
      flushInterval: "5s"
```

## 🔍 Monitoring and Observability

### Access Grafana

```bash
# Get Grafana URL
kubectl get svc grafana -n logging-system

# Port forward if LoadBalancer not available
kubectl port-forward svc/grafana -n logging-system 3000:3000
```

Default credentials: `admin/admin`

### Prometheus Metrics

The operator and all services expose Prometheus metrics:

- `logpipeline_reconcile_duration_seconds` - Reconciliation loop duration
- `logpipeline_reconcile_errors_total` - Reconciliation errors
- `logs_collected_total` - Total logs collected
- `logs_processed_total` - Total logs processed
- `logs_written_total` - Total logs written to sinks

### Check Pipeline Status

```bash
# Get pipeline status
kubectl get logpipelines -n logging

# Detailed status
kubectl describe logpipeline production-logs -n logging

# Check conditions
kubectl get logpipeline production-logs -n logging -o jsonpath='{.status.conditions}'
```

## 🧪 Testing

### Run Load Test

```bash
./scripts/load-test.sh
```

Generates synthetic log traffic to test pipeline performance.

### Verify Log Flow

```bash
# Check collector logs
kubectl logs -n logging -l component=collector

# Check processor logs
kubectl logs -n logging -l component=processor

# Check sink logs
kubectl logs -n logging -l component=sink

# Query Elasticsearch
kubectl port-forward svc/elasticsearch -n logging 9200:9200
curl "http://localhost:9200/logs-*/_search?size=10&pretty"
```

## 🏗️ Production Kubernetes Patterns Demonstrated

### 1. Custom Resource Definitions (CRDs)

- Extends Kubernetes API with domain-specific resources
- OpenAPI schema validation
- Status subresources for operational state
- Versioning and conversion webhooks ready

### 2. Operator Pattern

- Level-triggered reconciliation loops
- Idempotent operations
- Error handling with exponential backoff
- Owner references for garbage collection
- Status conditions for detailed state tracking

### 3. Resource Management

- Resource requests and limits on all components
- HorizontalPodAutoscaler ready (add based on metrics)
- PodDisruptionBudgets for high availability
- Node affinity and anti-affinity patterns

### 4. Service Mesh Integration

- Istio configurations for traffic management
- mTLS for service-to-service communication
- Circuit breakers and connection pooling
- Traffic splitting and canary deployments

### 5. Observability

- Prometheus metrics with custom exporters
- Structured logging with correlation IDs
- Distributed tracing ready (Jaeger integration)
- Health checks and readiness probes

### 6. GitOps Ready

- Declarative configuration
- Version-controlled manifests
- Helm charts for templating
- CI/CD pipeline examples

## 🔧 Troubleshooting

### Operator Not Creating Resources

```bash
# Check operator logs
kubectl logs -n logging-system -l app=logpipeline-operator

# Check RBAC permissions
kubectl auth can-i create deployments --as=system:serviceaccount:logging-system:logpipeline-operator

# Verify CRD installation
kubectl get crd logpipelines.logpipeline.k8s.io
```

### Pipeline in Failed State

```bash
# Check status message
kubectl get logpipeline <name> -n logging -o jsonpath='{.status.message}'

# Check conditions
kubectl describe logpipeline <name> -n logging

# Check created resources
kubectl get deployments,services -n logging -l pipeline=<name>
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n logging

# Check metrics
kubectl port-forward svc/prometheus -n logging-system 9090:9090
# Visit http://localhost:9090

# Check Kafka lag
kubectl exec -it kafka-0 -n logging -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --all-groups
```

## 🧹 Cleanup

```bash
# Remove all resources
./scripts/cleanup.sh

# Delete kind cluster
kind delete cluster --name logpipeline
```

## 📚 Kubernetes Concepts Covered

- **Custom Controllers**: Reconciliation loops, event handling, status management
- **CRDs**: Schema design, validation, versioning, subresources
- **Operator Pattern**: Level-triggered vs edge-triggered, idempotency, error handling
- **RBAC**: ServiceAccounts, Roles, ClusterRoles, RoleBindings
- **Resource Management**: Requests, limits, QoS classes, autoscaling
- **Service Mesh**: Istio gateways, virtual services, destination rules
- **Observability**: Prometheus, Grafana, custom metrics, health checks
- **High Availability**: Leader election, pod disruption budgets, anti-affinity
- **State Management**: StatefulSets, persistent volumes, data consistency

## 🎯 Production Considerations

1. **Multi-tenancy**: Namespace isolation, network policies, RBAC per tenant
2. **Security**: Pod security policies, secrets management, mTLS
3. **Disaster Recovery**: Backup strategies, multi-region, data replication
4. **Capacity Planning**: Resource quotas, limit ranges, cluster autoscaling
5. **Cost Optimization**: Right-sizing, spot instances, resource bin packing
6. **Compliance**: Audit logging, encryption at rest, data retention policies

## 📖 Further Reading

- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Custom Resource Definitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)
- [Controller Runtime](https://github.com/kubernetes-sigs/controller-runtime)
- [Kubebuilder Book](https://book.kubebuilder.io/)
- [Operator SDK](https://sdk.operatorframework.io/)

## 🤝 Contributing

This is a learning project demonstrating production Kubernetes patterns. Contributions welcome!

## 📄 License

MIT License - See LICENSE file for details
