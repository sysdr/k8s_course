# Internal Developer Platform (IDP) - Kubernetes Self-Service Platform

A production-grade Internal Developer Platform built on Kubernetes that abstracts infrastructure complexity while maintaining operational control.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Developer Portal (React)                     │
│          https://platform.company.com                           │
└────────────────────┬────────────────────────────────────────────┘
                     │ GraphQL/REST API
┌────────────────────▼────────────────────────────────────────────┐
│                  Platform API (FastAPI)                         │
│  - Service Orchestration  - Namespace Management               │
│  - Policy Enforcement     - Cost Attribution                   │
└────────────┬───────────────────────┬───────────────────────────┘
             │                       │
    ┌────────▼────────┐     ┌────────▼────────┐
    │  Kubernetes      │     │    ArgoCD       │
    │  API Server      │     │  GitOps Engine  │
    └────────┬────────┘     └────────┬────────┘
             │                       │
    ┌────────▼───────────────────────▼────────┐
    │         Kubernetes Cluster               │
    │  ┌──────────────┐  ┌──────────────┐    │
    │  │ team-backend │  │ team-frontend│    │
    │  │  Namespace   │  │   Namespace  │    │
    │  └──────────────┘  └──────────────┘    │
    │  ┌──────────────────────────────────┐  │
    │  │    Monitoring (Prometheus)       │  │
    │  └──────────────────────────────────┘  │
    └─────────────────────────────────────────┘
```

## Features

### Developer Self-Service
- **One-Click Deployments**: Deploy services with a single API call or UI click
- **Multi-Runtime Support**: Python, Node.js, Go with optimized base images
- **Auto-Scaling**: Horizontal Pod Autoscaler configuration based on CPU/memory
- **Zero-Downtime Deployments**: Rolling updates with health checks

### Platform Operations
- **Multi-Tenancy**: Strict namespace isolation with NetworkPolicies
- **Resource Quotas**: Per-team CPU/memory limits with usage tracking
- **Cost Attribution**: Team-level resource costs and optimization recommendations
- **GitOps Integration**: ArgoCD for declarative deployments

### Security & Compliance
- **Pod Security Standards**: Enforced security contexts (non-root, read-only filesystem)
- **Network Isolation**: Default-deny NetworkPolicies between teams
- **RBAC**: Fine-grained permissions per team namespace
- **Secret Management**: Kubernetes Secrets with encryption at rest

### Observability
- **Metrics**: Prometheus ServiceMonitors auto-generated for all services
- **Logging**: Centralized log aggregation (Loki/Elasticsearch)
- **Tracing**: Distributed tracing with Jaeger integration
- **Dashboards**: Pre-built Grafana dashboards for platform and services

## Quick Start

### Prerequisites

- Kubernetes 1.28+ cluster (kind, minikube, or cloud provider)
- kubectl configured
- Helm 3.12+
- Docker (for building images)

### Local Development Setup

1. **Create local Kubernetes cluster**:
```bash
cd scripts
./setup-cluster.sh
```

This creates a kind cluster with:
- Ingress controller (Nginx)
- Metrics server
- Prometheus operator
- ArgoCD

2. **Deploy the platform**:
```bash
./deploy.sh
```

This deploys:
- Platform API (FastAPI backend)
- Developer Portal (React frontend)
- ArgoCD with platform configuration
- Monitoring stack (Prometheus, Grafana)

3. **Access the platform**:
```bash
# Get platform URLs
kubectl get ingress -n platform-frontend

# Port-forward for local access
kubectl port-forward -n platform-system svc/platform-api 8000:80
kubectl port-forward -n platform-frontend svc/developer-portal 3000:80
```

- Platform API: http://localhost:8000/api/docs
- Developer Portal: http://localhost:3000
- Grafana: http://localhost:3001 (admin/admin)

### Creating Your First Service

#### Via API:

```bash
curl -X POST http://localhost:8000/api/v1/services \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "my-api",
    "team": "backend",
    "repository": "github.com/company/my-api",
    "runtime": "python3.11",
    "scaling": {
      "minReplicas": 2,
      "maxReplicas": 10,
      "targetCPU": 70
    },
    "resources": {
      "tier": "standard"
    },
    "networking": {
      "public": true,
      "domains": ["my-api.example.com"]
    },
    "observability": {
      "metrics": true,
      "tracing": true
    }
  }'
```

#### Via WebService CRD:

```yaml
apiVersion: platform.company.com/v1
kind: WebService
metadata:
  name: my-api
  namespace: team-backend
spec:
  repository: github.com/company/my-api
  runtime: python3.11
  scaling:
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 70
  resources:
    tier: standard
  networking:
    public: true
    domains:
      - my-api.example.com
  observability:
    metrics: true
    tracing: true
```

Apply with:
```bash
kubectl apply -f my-service.yaml
```

## Project Structure

```
idp-platform/
├── platform-api/              # FastAPI backend service
│   ├── src/
│   │   ├── controllers/       # API route handlers
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic
│   │   └── main.py           # Application entry point
│   ├── Dockerfile
│   └── requirements.txt
├── platform-portal/           # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   └── services/         # API clients
│   └── package.json
├── k8s/                       # Kubernetes manifests
│   ├── platform-crds/        # Custom Resource Definitions
│   ├── platform-system/      # Platform control plane
│   ├── argocd-setup/         # GitOps configuration
│   ├── monitoring/           # Prometheus, Grafana
│   └── teams/                # Team namespace templates
├── helm/                      # Helm charts
│   └── idp-platform/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── scripts/                   # Operational scripts
│   ├── setup-cluster.sh      # Local cluster setup
│   ├── deploy.sh             # Deploy platform
│   └── cleanup.sh            # Teardown
└── docs/                      # Documentation
    ├── architecture/
    ├── api/
    └── runbooks/
```

## Configuration

### Resource Tiers

The platform provides four resource tiers:

| Tier | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------|-------------|-----------|----------------|--------------|
| small | 500m | 1000m | 512Mi | 1Gi |
| standard | 1000m | 2000m | 1Gi | 2Gi |
| large | 2000m | 4000m | 4Gi | 8Gi |
| xlarge | 4000m | 8000m | 8Gi | 16Gi |

### Team Quotas

Default quotas per team namespace:

- CPU Requests: 100 cores
- Memory Requests: 200Gi
- Persistent Volume Claims: 10
- Load Balancers: 5
- Pods: 100

## Monitoring and Observability

### Metrics

All services automatically expose Prometheus metrics at `/metrics`:
- Request rate, latency percentiles (p50, p95, p99)
- Error rates by endpoint
- Resource utilization (CPU, memory)

### Dashboards

Pre-built Grafana dashboards:
- Platform Overview: Cluster-wide metrics
- Team Dashboard: Per-team resource usage and costs
- Service Health: Individual service metrics

### Alerts

AlertManager rules configured for:
- High error rates (>5% 5xx responses)
- Pod crash loops
- Resource quota exhaustion
- HPA at max replicas

## Production Deployment

### Multi-Cluster Setup

For production, deploy across multiple clusters:

```bash
# Deploy to production cluster
kubectl config use-context prod-us-east-1
./scripts/deploy.sh --environment production

# Deploy to DR cluster
kubectl config use-context prod-eu-west-1
./scripts/deploy.sh --environment production
```

### Disaster Recovery

Platform state is backed up with Velero:
```bash
# Install Velero
velero install --provider aws --bucket platform-backups

# Create backup schedule
velero schedule create platform-daily \
  --schedule="0 2 * * *" \
  --include-namespaces=platform-system,argocd,monitoring
```

Recovery time objectives:
- Platform control plane: <30 minutes
- Team namespaces: <2 hours

### Scaling Considerations

Platform overhead scales with application count:
- Base: 4 CPU / 8GB RAM
- Per 100 applications: +2 CPU / +4GB RAM

Node autoscaling buffer: 30-60s for pod scheduling

## Security

### Authentication

Platform API uses OIDC for authentication:
```yaml
OIDC_PROVIDER_URL: https://auth.company.com
OIDC_CLIENT_ID: platform-api
```

### Authorization

RBAC policies per team:
- Team members: Deploy, view logs, scale within limits
- Platform admins: Full cluster access
- Viewers: Read-only access

### Network Policies

Default-deny between team namespaces:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: team-isolation
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          team: backend  # Only same team
```

## Troubleshooting

### Service won't deploy

1. Check platform API logs:
```bash
kubectl logs -n platform-system deployment/platform-api
```

2. Verify team quota:
```bash
kubectl get resourcequota -n team-backend
```

3. Check pod events:
```bash
kubectl describe pod -n team-backend <pod-name>
```

### ArgoCD sync failures

1. Check Application status:
```bash
kubectl get application -n argocd
argocd app get <app-name>
```

2. Force sync:
```bash
argocd app sync <app-name> --force
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

Internal use only - Company Proprietary

## Support

- Slack: #platform-support
- Email: platform-team@company.com
- Runbooks: [docs/runbooks/](docs/runbooks/)
