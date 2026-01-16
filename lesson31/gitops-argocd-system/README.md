# GitOps Platform with ArgoCD

Production-grade GitOps implementation using ArgoCD for declarative Kubernetes deployments.

## Architecture

This system implements a complete GitOps workflow:

- **ArgoCD**: Continuous deployment operator that syncs Git state to cluster state
- **Metrics Aggregator**: Python FastAPI service polling ArgoCD API for metrics
- **Event Processor**: Processes ArgoCD webhooks and maintains deployment history
- **Dashboard**: React-based real-time monitoring interface
- **Service Mesh**: Istio for secure service-to-service communication
- **Monitoring**: Prometheus/Grafana stack for observability

## Prerequisites

- Docker
- kubectl
- kind (or any Kubernetes cluster)
- Helm 3.x
- Git

## Quick Start

### 1. Setup Kubernetes Cluster

```bash
cd scripts
./setup-cluster.sh
```

This creates a local kind cluster with 1 control plane and 2 worker nodes.

### 2. Install ArgoCD

```bash
./install-argocd.sh
```

This installs ArgoCD and displays your admin credentials.

### 3. Build Application Images

```bash
./build.sh
```

This builds all Docker images and loads them into the kind cluster.

### 4. Deploy GitOps Platform

```bash
./deploy.sh
```

This creates ArgoCD Applications that will sync your manifests from Git.

### 5. Setup Monitoring

```bash
./monitoring-setup.sh
```

This installs Prometheus Operator and configures ServiceMonitors.

## Accessing Services

### ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open https://localhost:8080 (accept self-signed cert)

### GitOps Dashboard

```bash
kubectl port-forward svc/dashboard -n gitops-apps-prod 8081:80
```

Open http://localhost:8081

### Grafana

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 8082:80
```

Open http://localhost:8082 (admin/prom-operator)

### Prometheus

```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
```

## GitOps Workflow

### Directory Structure

```
gitops-repo/
├── apps/
│   ├── base/                    # Base Kubernetes manifests
│   └── overlays/
│       ├── dev/                 # Dev environment customizations
│       ├── staging/             # Staging environment
│       └── prod/                # Production environment
├── argocd-apps/                 # ArgoCD Application definitions
└── infrastructure/              # Infrastructure manifests
    ├── namespaces/
    └── monitoring/
```

### Making Changes

1. Edit manifests in `gitops-repo/`
2. Commit and push to Git
3. ArgoCD detects changes within 3 minutes
4. ArgoCD automatically syncs cluster state

Example:

```bash
cd gitops-repo/apps/base
# Edit deployment.yaml
vim deployment.yaml

git add .
git commit -m "Scale metrics-aggregator to 5 replicas"
git push origin main

# Watch ArgoCD sync
kubectl get applications -n argocd -w
```

### Manual Sync

```bash
# Sync specific application
argocd app sync gitops-platform-prod

# Or via kubectl
kubectl patch application gitops-platform-prod \
  -n argocd \
  --type merge \
  -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

## Environment Management

### Dev Environment

- Single replicas
- Minimal resources
- Auto-prune enabled
- Namespace: `gitops-apps-dev`

### Staging Environment

- 2 replicas
- Moderate resources
- Auto-prune enabled
- Namespace: `gitops-apps-staging`

### Production Environment

- 3+ replicas
- High resources
- Manual prune (safer)
- Namespace: `gitops-apps-prod`

## ArgoCD Configuration

### Application Sync Policies

```yaml
syncPolicy:
  automated:
    prune: true        # Delete resources not in Git
    selfHeal: true     # Revert manual changes
    allowEmpty: false  # Prevent empty syncs
  syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

### RBAC Roles

- **Admin**: Full access to all ArgoCD resources
- **Developer**: Read applications, trigger syncs
- **Readonly**: View-only access

## Monitoring & Observability

### Key Metrics

- `argocd_app_sync_total`: Application sync count by status
- `argocd_app_health_status`: Application health (1=Healthy, 0=Degraded, -1=Missing)
- `argocd_app_sync_duration_seconds`: Sync duration histogram
- `argocd_app_out_of_sync`: Applications not synchronized

### Alerts

- **ArgoCDAppOutOfSync**: Application out of sync > 5 minutes
- **ArgoCDAppSyncFailure**: Application sync failed
- **ArgoCDAppUnhealthy**: Application unhealthy > 10 minutes

### Grafana Dashboards

Pre-configured dashboards for:
- Application sync status
- Deployment velocity
- Sync duration trends
- Health status over time

## Production Considerations

### High Availability

- ArgoCD installed in HA mode with multiple replicas
- Redis for caching cluster state
- Multiple application controllers for scalability

### Disaster Recovery

1. Git repositories are primary backup
2. Velero backups of ArgoCD namespace (6-hour schedule)
3. External secret management (Vault/AWS Secrets Manager)
4. Multi-region ArgoCD instances for global deployments

### Security

- RBAC with SSO integration (Dex)
- Separate ArgoCD Projects per team
- Istio mTLS for service-to-service communication
- Network Policies for pod-to-pod isolation
- Secrets stored in external secret managers

### Scaling

- Single ArgoCD handles ~2000 Applications
- Use sharding for >2000 Applications
- Separate ArgoCD instances per environment/team
- ApplicationSets for managing large application portfolios

## Troubleshooting

### Application Not Syncing

```bash
# Check application status
kubectl describe application gitops-platform-prod -n argocd

# View sync logs
kubectl logs -n argocd deployment/argocd-application-controller

# Force refresh
argocd app sync gitops-platform-prod --force
```

### Sync Failure

```bash
# Check sync status
argocd app get gitops-platform-prod

# View sync result
kubectl get application gitops-platform-prod -n argocd -o yaml

# Check manifest rendering
argocd app manifests gitops-platform-prod
```

### Drift Detection

```bash
# Check if resources drifted from Git
argocd app diff gitops-platform-prod

# Sync to restore Git state
argocd app sync gitops-platform-prod
```

## Testing GitOps Workflow

```bash
cd scripts
./test-sync.sh
```

This script modifies replica count and demonstrates the sync workflow.

## Cleanup

```bash
cd scripts
./cleanup.sh
```

This removes all deployed resources and optionally deletes the cluster.

## Architecture Decisions

### Why ArgoCD?

- **Pull-based model**: No cluster credentials in CI/CD
- **Declarative**: Git as single source of truth
- **Automated**: Continuous reconciliation loops
- **Auditable**: Complete Git history of all changes
- **Multi-cluster**: Single ArgoCD manages multiple clusters

### Why Kustomize Overlays?

- **DRY principle**: Base manifests shared across environments
- **Environment-specific**: Patches for different environments
- **No templating**: Native Kubernetes YAML
- **Composable**: Build complex manifests from simple bases

### Why Separate Event Processor?

- **Durability**: Webhook events stored in database
- **Audit trail**: Complete deployment history
- **Analytics**: Deployment velocity metrics
- **Debugging**: Historical context for failures

## Real-World Scale Examples

- **Netflix**: 100,000+ containers, ArgoCD for multi-region deployments
- **Intuit**: 14 ArgoCD instances, 8,000+ Applications, 500+ daily commits
- **Ticketmaster**: 70% reduction in deployment incidents with GitOps
- **Spotify**: 200-person infra team supporting 1,500+ engineers via GitOps self-service

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [Kustomize](https://kustomize.io/)
- [Istio Service Mesh](https://istio.io/)
- [Prometheus Operator](https://prometheus-operator.dev/)
