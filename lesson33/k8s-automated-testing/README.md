# Kubernetes Automated Testing Platform

Production-grade e-commerce platform with comprehensive automated testing orchestration using Kubernetes Jobs.

## 🏗️ System Architecture

This platform demonstrates production testing patterns used at scale:

- **Microservices**: Product, Order, Payment services with FastAPI
- **Test Orchestration**: Integration, smoke, and performance tests as K8s Jobs
- **Quality Gates**: Automated deployment blocking based on test results
- **Result Aggregation**: Centralized test result collection and reporting
- **Progressive Testing**: Multi-phase test execution with dependencies

### Services

- **Product Service** (Port 8000): Product catalog with Redis caching
- **Order Service** (Port 8001): Order orchestration with service communication
- **Payment Service** (Port 8002): Payment processing simulation
- **Test Results Aggregator** (Port 8003): Centralized test result management

## 🚀 Quick Start

### Prerequisites

- Docker
- Kubernetes cluster (kind, minikube, or cloud)
- kubectl
- jq (for parsing test results)

### 1. Build Images

```bash
./scripts/build.sh
```

This builds all service images and the test runner.

### 2. Setup Cluster

```bash
./scripts/setup-cluster.sh
```

Creates a kind cluster and loads images.

### 3. Deploy Services

```bash
./scripts/deploy.sh
```

Deploys all microservices to the `ecommerce` namespace.

### 4. Run Test Suite

```bash
./scripts/run-tests.sh
```

Executes complete test suite and checks quality gates.

## 📊 Test Suite Architecture

### Test Types

**Smoke Tests** (5 minutes)
- Basic health checks for all services
- Service availability validation
- Runs first to fail fast

**Integration Tests** (10 minutes)
- Complete order flow testing
- Service-to-service communication
- Stock reservation and payment processing
- Error handling and edge cases

**Performance Tests** (15 minutes)
- Load testing with k6
- Latency benchmarks (p95 < 500ms)
- Error rate validation (< 5%)
- Concurrent user simulation

### Test Execution Flow

```
Deployment → Smoke Tests → Integration Tests → Performance Tests → Quality Gate
     ↓            ↓              ↓                    ↓                  ↓
  Services    Fast Fail    Service Flow    Performance Check    Deploy/Block
```

### Quality Gates

Tests must meet these criteria to pass:

- **Pass Rate**: ≥ 95%
- **Failed Tests**: 0
- **Performance**: p95 < 500ms
- **Error Rate**: < 5%

## 🧪 Running Individual Tests

### Smoke Tests

```bash
kubectl apply -f k8s/jobs/smoke-tests.yaml
kubectl logs -f job/smoke-tests -n ecommerce
```

### Integration Tests

```bash
kubectl apply -f k8s/jobs/integration-tests.yaml
kubectl logs -f job/integration-tests -n ecommerce
```

### Performance Tests

```bash
kubectl apply -f k8s/jobs/performance-tests.yaml
kubectl logs -f job/performance-tests -n ecommerce
```

## 📈 Viewing Test Results

### Real-time Results

```bash
./scripts/view-test-results.sh
```

### Direct API Access

```bash
# Port forward aggregator
kubectl port-forward -n ecommerce svc/test-results-aggregator 8003:8003

# Get summary
curl http://localhost:8003/api/v1/results/summary | jq

# Get all results
curl http://localhost:8003/api/v1/results | jq

# Check quality gates
curl http://localhost:8003/api/v1/gate/check | jq
```

## 🎯 Key Testing Patterns

### 1. Test Jobs vs Regular Pods

Jobs provide completion semantics and failure detection:

```yaml
spec:
  backoffLimit: 0  # Don't retry - failures should fail
  activeDeadlineSeconds: 600  # 10 minute timeout
  ttlSecondsAfterFinished: 3600  # Auto-cleanup
```

### 2. Test Result Persistence

Results stored in ConfigMaps for audit trail:

```python
# Test submits results to aggregator
result = {
    "job_name": "integration-tests",
    "passed": 45,
    "failed": 2,
    "duration_ms": 12453
}
```

### 3. Quality Gate Implementation

```bash
# Check gates before deployment
GATE_STATUS=$(curl http://aggregator:8003/api/v1/gate/check)
if [ "$GATE_PASSED" != "true" ]; then
  exit 1  # Block deployment
fi
```

### 4. Test Isolation

Each test run gets dedicated namespace:

```yaml
metadata:
  name: test-run-${CI_COMMIT_SHA}
  labels:
    test-isolation: "true"
```

## 🔧 Configuration

### Environment Variables

**Product Service**:
- `REDIS_HOST`: Redis hostname (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)

**Order Service**:
- `PRODUCT_SERVICE_URL`: Product service endpoint
- `PAYMENT_SERVICE_URL`: Payment service endpoint

**Test Runner**:
- `JOB_NAME`: Test job identifier
- `TEST_RESULTS_URL`: Aggregator endpoint

### Resource Limits

Services configured with production-grade resources:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## 📦 Helm Deployment

### Install with Helm

```bash
helm install ecommerce helm/e-commerce-platform \
  --namespace ecommerce \
  --create-namespace \
  --set testing.enabled=true
```

### Upgrade with Tests

```bash
helm upgrade ecommerce helm/e-commerce-platform \
  --set testing.runOnDeploy=true
```

Tests run as Helm hooks after deployment.

## 🔍 Troubleshooting

### Test Job Failures

```bash
# View job logs
kubectl logs job/integration-tests -n ecommerce

# Describe job for events
kubectl describe job integration-tests -n ecommerce

# Check pod status
kubectl get pods -n ecommerce -l test-suite=integration
```

### Service Issues

```bash
# Check service health
kubectl exec -it deployment/product-service -n ecommerce -- \
  curl http://localhost:8000/health

# View service logs
kubectl logs -f deployment/product-service -n ecommerce
```

### Quality Gate Failures

```bash
# Get detailed results
curl http://localhost:8003/api/v1/results | jq \
  '.[] | select(.failed > 0)'

# View recent test history
curl http://localhost:8003/api/v1/results?test_suite=integration
```

## 🏢 Production Patterns

This implementation demonstrates patterns from scale:

**Google**: 5.5B tests/day using test sharding and result caching

**Netflix**: Continuous testing in production with shadow traffic

**Spotify**: 4,000 deployments/day with automated quality gates

**Uber**: Post-deployment smoke tests as Jobs with zero retries

**LinkedIn**: Contract tests every 15 minutes across 2,000+ services

### Key Learnings

1. **Jobs > Pods**: Completion semantics prevent silent failures
2. **No Retries**: `backoffLimit: 0` exposes real issues
3. **Result Persistence**: ConfigMaps provide audit trail
4. **Quality Gates**: Block bad deployments automatically
5. **Test Isolation**: Dedicated namespaces prevent interference

## 🧹 Cleanup

```bash
./scripts/cleanup.sh
```

Removes all resources. Optionally deletes namespace.

## 📚 Additional Resources

- **Kubernetes Jobs**: https://kubernetes.io/docs/concepts/workloads/controllers/job/
- **Testing at Scale**: Google's test infrastructure paper
- **Quality Gates**: Martin Fowler on deployment pipelines
- **Performance Testing**: k6 documentation

## 🎓 Learning Objectives

After completing this lesson, you should be able to:

- ✅ Implement multi-tier test suites as Kubernetes Jobs
- ✅ Configure test Jobs with proper timeouts and retry policies
- ✅ Build test result aggregation and reporting systems
- ✅ Implement automated quality gates for deployments
- ✅ Isolate test execution using Kubernetes namespaces
- ✅ Debug failed test Jobs and interpret results
- ✅ Scale testing patterns to production environments

## 🚀 Next Steps

1. Add contract testing with Pact
2. Implement test sharding for parallel execution
3. Add mutation testing for test quality validation
4. Build test result dashboards with Grafana
5. Integrate with CI/CD pipelines (GitHub Actions, ArgoCD)
6. Add chaos testing with Chaos Mesh
7. Implement canary testing before production rollout

---

**Course**: The Kubernetes Odyssey - Lesson 33: Automated Testing
**Difficulty**: Intermediate
**Duration**: 6-8 hours
