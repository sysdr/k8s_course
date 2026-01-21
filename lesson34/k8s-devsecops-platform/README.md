# DevSecOps Kubernetes Platform

A production-grade DevSecOps platform demonstrating security scanning, policy enforcement, and automated compliance in Kubernetes.

## 🏗 System Architecture

This platform implements a complete DevSecOps pipeline with:

- **Container Security**: Trivy vulnerability scanning integrated into CI/CD
- **Policy Enforcement**: Kyverno policies for pod security standards
- **Network Security**: Zero-trust networking with NetworkPolicies
- **Runtime Security**: Security contexts and capability restrictions
- **Secrets Management**: Kubernetes secrets with external integration patterns
- **Monitoring**: Prometheus metrics and health checks

### Components

- **API Gateway**: Entry point with rate limiting and authentication
- **Auth Service**: JWT token generation and validation
- **Log Processor**: Log ingestion and storage
- **Analytics Service**: Real-time log analytics
- **Frontend**: React dashboard for system monitoring

## 🔒 Security Features

### 1. Container Image Scanning (Trivy)

```bash
# Scan all images for vulnerabilities
./security/trivy/scan-images.sh

# Scan specific image
trivy image api-gateway:latest --severity CRITICAL,HIGH
```

### 2. Policy Enforcement (Kyverno)

Enforced policies:
- ✅ Run as non-root user
- ✅ Read-only root filesystem
- ✅ Drop all capabilities
- ✅ Require resource limits
- ✅ Disallow privileged containers
- ✅ Require standard labels

### 3. Network Policies

- Default deny all traffic
- Explicit allow rules for service-to-service communication
- DNS resolution allowed to kube-system

### 4. Pod Security

- Security contexts on all pods
- No privileged containers
- Capability dropping
- Non-root users
- Read-only filesystems

## 🚀 Quick Start

### Prerequisites

- Docker
- kubectl
- kind (or minikube)
- Trivy

### Setup

```bash
# 1. Create local Kubernetes cluster
./scripts/setup-cluster.sh

# 2. Build and load container images
./scripts/build.sh

# 3. Run security scans (optional but recommended)
./security/trivy/scan-images.sh

# 4. Deploy the platform
./scripts/deploy.sh

# 5. Run integration tests
./scripts/test.sh
```

### Access the Application

```bash
# Port forward to access services locally
kubectl port-forward -n devsecops svc/frontend 3000:80
kubectl port-forward -n devsecops svc/api-gateway 8000:8000
```

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Test Login

Use these credentials in the frontend:
- Username: `admin` Password: `admin123`
- Username: `user` Password: `user123`

## 📊 Monitoring

### View Prometheus Metrics

```bash
# API Gateway metrics
kubectl port-forward -n devsecops svc/api-gateway 8000:8000
curl http://localhost:8000/metrics

# Auth Service metrics
kubectl port-forward -n devsecops svc/auth-service 8001:8001
curl http://localhost:8001/metrics
```

### Check Pod Status

```bash
kubectl get pods -n devsecops
kubectl get all -n devsecops
```

### View Security Policy Reports

```bash
# Get policy violations
kubectl get policyreport -A

# Describe specific policy
kubectl describe clusterpolicy require-non-root-user
```

## 🧪 Testing

### Security Scanning

```bash
# Scan all images
./security/trivy/scan-images.sh

# Scan Kubernetes manifests
trivy config k8s/base/

# Scan for secrets in code
trivy fs .
```

### Policy Validation

```bash
# Test policies against manifests
kyverno apply k8s/security/kyverno-policies.yaml \
  --resource k8s/base/ \
  --detailed-results
```

### Integration Tests

```bash
# Run all integration tests
./scripts/test.sh

# Manual API testing
kubectl port-forward -n devsecops svc/api-gateway 8000:8000

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token for authenticated requests
TOKEN="your-jwt-token-here"
curl http://localhost:8000/analytics/summary \
  -H "Authorization: Bearer $TOKEN"
```

## 📁 Project Structure

```
k8s-devsecops-platform/
├── services/               # Microservices
│   ├── api-gateway/       # FastAPI gateway
│   ├── auth-service/      # Authentication service
│   ├── log-processor/     # Log processing
│   └── analytics-service/ # Analytics engine
├── frontend/              # React frontend
├── k8s/                   # Kubernetes manifests
│   ├── base/             # Core deployments
│   ├── security/         # Kyverno policies
│   └── network-policies/ # Network security
├── security/             # Security tools
│   └── trivy/           # Trivy configuration
├── ci-cd/               # CI/CD pipelines
├── scripts/             # Operational scripts
└── docs/                # Documentation
```

## 🔐 Security Best Practices

### Image Security
- Multi-stage Docker builds
- Non-root users in containers
- Minimal base images (Python slim)
- No secrets in images
- Regular vulnerability scanning

### Kubernetes Security
- Pod Security Standards (Restricted)
- Network policies for zero-trust
- RBAC with least privilege
- Resource quotas and limits
- Security contexts on all pods

### Secrets Management
- Kubernetes Secrets for basic use
- External Secrets Operator integration pattern
- Secrets rotation strategy
- No secrets in environment variables

## 🔧 Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n devsecops

# View pod logs
kubectl logs -n devsecops <pod-name>

# Describe pod for events
kubectl describe pod -n devsecops <pod-name>
```

### Policy violations

```bash
# Check which policies are failing
kubectl get policyreport -A

# View policy details
kubectl describe clusterpolicy <policy-name>

# Check pod events
kubectl get events -n devsecops --sort-by='.lastTimestamp'
```

### Network issues

```bash
# Test service connectivity
kubectl run -it --rm debug --image=nicolaka/netshoot -n devsecops -- /bin/bash

# Inside the debug pod:
# curl http://api-gateway:8000/health
# curl http://auth-service:8001/health
```

### Image pull issues

```bash
# Check if images are loaded in kind
docker exec -it devsecops-cluster-control-plane crictl images

# Reload images if needed
./scripts/build.sh
```

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] All images scanned with Trivy (no CRITICAL vulnerabilities)
- [ ] Kyverno policies validated against manifests
- [ ] Resource limits set appropriately for workload
- [ ] Secrets migrated to external secrets manager (Vault/AWS Secrets Manager)
- [ ] Network policies tested and validated
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery plan in place
- [ ] SSL/TLS certificates configured for ingress
- [ ] Authentication integrated with corporate identity provider

### Configuration Changes for Production

1. **Secrets**: Replace Kubernetes Secrets with External Secrets Operator
2. **Ingress**: Configure proper ingress with SSL/TLS termination
3. **Monitoring**: Deploy full Prometheus/Grafana stack
4. **Logging**: Integrate with centralized logging (ELK/Splunk)
5. **Autoscaling**: Tune HPA metrics based on actual load patterns
6. **Resource Limits**: Adjust based on production profiling
7. **Image Registry**: Use private registry with image signing
8. **High Availability**: Increase replicas, configure pod disruption budgets

## 📚 Additional Resources

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Kyverno Documentation](https://kyverno.io/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [OWASP Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)

## 🧹 Cleanup

```bash
# Delete all resources
./scripts/cleanup.sh

# Delete the kind cluster
kind delete cluster --name devsecops-cluster
```

## 📝 CI/CD Integration

The platform includes GitHub Actions workflow (`.github/workflows/devsecops.yml`) that:

1. **Security Scanning**: Trivy scans on every commit
2. **Policy Validation**: Kyverno policy checks
3. **Image Signing**: Cosign integration (requires setup)
4. **Integration Tests**: Automated testing in kind cluster
5. **Deployment**: Automated staging/production deployment

## 🤝 Contributing

Contributions welcome! Please ensure:
- All images pass Trivy scans (no CRITICAL vulnerabilities)
- Kubernetes manifests pass Kyverno policy validation
- Integration tests pass
- Documentation updated

## 📄 License

MIT License - see LICENSE file for details
