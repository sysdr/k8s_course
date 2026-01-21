# GitOps Drift Detection System

Production-grade ArgoCD debugging environment for learning GitOps drift detection and resolution patterns.

## System Architecture

This system demonstrates:
- **ArgoCD GitOps** workflow with automated sync policies
- **Intentional drift scenarios** for hands-on debugging practice
- **Complete observability** with Prometheus and Grafana
- **Multi-service architecture** with API, Frontend, and Worker services
- **Enhanced dashboard** with sync strategy visibility, health/sync distinction, drift classification, and reconciliation tracking

### Architecture Components

**Applications:**
1. **API Service** - FastAPI backend with drift event tracking and enhanced status reporting
2. **Frontend Dashboard** - React dashboard with comprehensive drift detection features
3. **Worker Service** - Background job processor (intentional drift target for debugging)

**Infrastructure:**
- **ArgoCD** - GitOps controller for declarative deployments
- **Redis** - State storage for drift events
- **Prometheus** - Metrics collection for applications and ArgoCD
- **Grafana** - Visualization dashboards

### GitOps Workflow

```
Git Repository (Source of Truth)
        ↓
    ArgoCD (Reconciliation Loop)
        ↓
    Kubernetes Cluster (Live State)
        ↓
    Drift Detection (Compare Git vs Live)
```

## Prerequisites

- Docker
- kind (Kubernetes in Docker)
- kubectl
- WSL2 (if running on Windows)
- ArgoCD CLI (optional but recommended)

## Quick Start

### 1. Setup Cluster

```bash
cd scripts
./setup-cluster.sh
```

This creates a kind cluster with:
- 3 namespaces: `production`, `monitoring`, `argocd`
- Port mappings for local access

### 2. Install ArgoCD

```bash
./install-argocd.sh
```

Save the admin password displayed in the output.

### 3. Build Application Images

```bash
./build.sh
```

Builds and loads images into kind cluster:
- `api-service:latest`
- `frontend:latest`
- `worker:latest`

### 4. Deploy Applications

```bash
./deploy.sh
```

Deploys:
- Infrastructure (Redis)
- Monitoring stack (Prometheus, Grafana)
- Applications via ArgoCD

### 5. Access Dashboard

**From Windows PowerShell:**
```powershell
wsl kubectl port-forward -n production svc/frontend 3000:80
```

**From WSL/Linux:**
```bash
kubectl port-forward -n production svc/frontend 3000:80
```

Then open: **http://localhost:3000**

**Alternative (Windows):** Double-click `START_DASHBOARD.bat`

## Dashboard Features

The enhanced dashboard provides comprehensive GitOps drift detection with the following features:

### 1. Sync Strategy Visibility

- **Sync Mode**: Shows Auto, Manual, or Delay mode with color-coded badges
- **Auto-Heal Status**: Clear ON/OFF indicator
- **Drift Grace Window**: 30-minute countdown timer with visual progress bar
- **Real-time Updates**: Automatically refreshes every 30 seconds

### 2. Health vs Sync Distinction

- **Separate Status Badges**: 
  - Health Status (🏥) - Pods running and responding
  - Sync Status (🔄) - Matches Git configuration
- **Tooltips**: Hover to see explanations
- **Info Alerts**: Highlights "Healthy but OutOfSync" scenarios
- **Color Coding**: Green (good), Warning (out of sync), Error (unhealthy)

### 3. Drift Classification

- **Drift Type**: Intentional, Accidental, or Malicious
- **Risk Level**: Low, Medium, or High
- **Color-Coded Chips**: Easy visual identification
- **Table Integration**: Enhanced drift events table with classification columns

### 4. Reconciliation Outcome Tracking

- **Last Action Panel**: Shows what action was taken (Revert, Git Update, etc.)
- **History Icon**: Visual indicator
- **Timestamp**: When the action occurred
- **Action Types**: 
  - "Reverted to Git"
  - "Git updated and synced"
  - "Manual kubectl scale (pending resolution)"

## Access URLs

### Frontend Dashboard (Main UI)
```bash
# Windows PowerShell
wsl kubectl port-forward -n production svc/frontend 3000:80

# WSL/Linux
kubectl port-forward -n production svc/frontend 3000:80
```
**URL:** http://localhost:3000

### API Service (REST API)
```bash
wsl kubectl port-forward -n production svc/api-service 8000:8000
```
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics

### ArgoCD UI (GitOps Management)
```bash
wsl kubectl port-forward -n argocd svc/argocd-server 8080:443
```
- **URL:** https://localhost:8080
- **Username:** admin
- **Password:** (from install-argocd.sh output)

### Grafana (Monitoring)
```bash
wsl kubectl port-forward -n monitoring svc/grafana 3001:3000
```
- **URL:** http://localhost:3001
- **Username:** admin
- **Password:** admin

### Prometheus (Metrics)
```bash
wsl kubectl port-forward -n monitoring svc/prometheus 9090:9090
```
- **URL:** http://localhost:9090

## Debugging Exercise: Resolve ArgoCD Drift

### Scenario

A production incident occurred where an engineer manually scaled the worker deployment to handle a traffic spike. Your task is to detect and resolve the drift.

### Step 1: Introduce Drift

```bash
cd scripts
./introduce-drift.sh
```

This script:
- Scales worker deployment from 2 to 8 replicas
- Increases memory limit from 512Mi to 1Gi
- Simulates manual kubectl changes during an incident

### Step 2: Detect the Drift

**Using Dashboard:**
- Open http://localhost:3000
- Worker deployment shows:
  - Sync Status: OutOfSync
  - Health Status: Healthy (pods work but config differs)
  - Drift Type: Intentional
  - Risk Level: Medium
  - Grace Window: 25 minutes remaining

**Using ArgoCD CLI:**
```bash
argocd app get worker
# Output: Sync Status: OutOfSync, Health Status: Healthy

argocd app diff worker
# Shows: spec.replicas: 2 (Git) → 8 (Live)
```

### Step 3: Investigate

Query Kubernetes events:
```bash
kubectl get events -n production --field-selector involvedObject.name=worker
```

View deployment history:
```bash
kubectl rollout history deployment/worker -n production
```

### Step 4: Resolution Options

#### Option A: Revert to Git

```bash
argocd app sync worker --force
kubectl get deployment worker -n production
# Should show: 2 replicas, 512Mi memory
```

#### Option B: Commit the Change to Git

```bash
# Edit the Git manifest
vim gitops/base/worker-deployment.yaml

# Update:
# spec.replicas: 2 → 8
# resources.limits.memory: 512Mi → 1Gi

# Commit and push
git add gitops/base/worker-deployment.yaml
git commit -m "Production scaling: Increase worker replicas and memory"
git push origin main

# ArgoCD will detect and sync
argocd app sync worker
```

## Production Patterns Demonstrated

### 1. Sync Strategies

**Manual Sync**
- Engineer approves every change
- Safest for production
- Slower deployment velocity

**Auto-Sync**
- Automatically reverts drift
- Fast reconciliation
- Can revert emergency fixes

**30-Minute Drift Window Pattern**
- Engineer makes kubectl change during incident
- 30-minute timer starts
- Engineer must commit to Git within window
- After 30 minutes, auto-sync reverts if not committed

### 2. Health vs Sync Distinction

**Key Insight:** "Healthy does NOT always mean synced"

- **Health Status**: Pods are running and responding to requests
- **Sync Status**: Configuration matches Git repository
- **Scenario**: Pods can be healthy while configuration drifts from Git

The dashboard clearly shows both statuses separately.

### 3. Drift Classification

**Intentional Drift**
- Planned changes during incidents
- Emergency scaling or configuration updates
- Should be committed to Git within grace window

**Accidental Drift**
- Unintended changes
- Configuration mistakes
- Should be reverted immediately

**Malicious Drift**
- Unauthorized changes
- Security concerns
- Requires immediate investigation and reversion

### 4. Reconciliation Tracking

Track what actions were taken:
- **Reverted to Git**: Manual change was reverted
- **Git updated and synced**: Change was committed and synced
- **Pending resolution**: Change detected, awaiting decision

## Monitoring and Observability

### Prometheus Metrics

```promql
# Sync status by application
argocd_app_info{sync_status="OutOfSync"}

# Sync duration
histogram_quantile(0.95, argocd_app_sync_duration_seconds_bucket)

# Failed syncs
rate(argocd_app_sync_total{phase="Failed"}[5m])

# API metrics
api_requests_total{endpoint="/drift-events"}
drift_events_total{namespace="production"}
```

### Grafana Dashboards

Pre-configured dashboards:
- **ArgoCD Overview** - Sync status across all apps
- **Drift Detection** - OutOfSync applications over time
- **Application Health** - Deployment status and pod health

## Troubleshooting

### Dashboard Not Accessible (ERR_CONNECTION_REFUSED)

**Solution:** Port-forward must be running from Windows PowerShell (not WSL):

```powershell
wsl kubectl port-forward -n production svc/frontend 3000:80
```

**Keep the PowerShell window open** while accessing the dashboard.

### kubectl Connection Errors in Windows

Windows kubectl may try to connect to Docker Desktop. Use WSL kubectl:

```powershell
wsl kubectl port-forward -n production svc/frontend 3000:80
```

### ArgoCD Shows Synced but Drift Exists

**Cause:** `ignoreDifferences` config hiding actual drift

**Solution:** Review and minimize ignore rules in application manifests.

### Self-Heal Reverts Emergency Fixes

**Solution:** Implement break-glass override:

```bash
# Pause auto-sync temporarily
argocd app set worker --sync-policy none

# Make emergency change
kubectl scale deployment worker -n production --replicas=20

# Resume after incident resolved
argocd app set worker --sync-policy automated
```

## Debugging Checklist

When investigating drift:

- [ ] Check dashboard for sync status and drift classification
- [ ] View ArgoCD application sync status: `argocd app get <app-name>`
- [ ] View detailed diff: `argocd app diff <app-name>`
- [ ] Query Kubernetes events for resource changes
- [ ] Check drift grace window countdown in dashboard
- [ ] Verify Git commit history for intended state
- [ ] Decide: Revert to Git or commit the change?
- [ ] Check last action taken in dashboard
- [ ] Update runbooks if process gap found

## Cleanup

```bash
cd scripts
./cleanup.sh
```

Deletes the kind cluster and all resources.

## Project Structure

```
gitops-drift-debug/
├── apps/
│   ├── api-service/          # FastAPI backend
│   ├── frontend/             # React dashboard
│   └── worker/               # Background worker
├── gitops/
│   ├── applications/         # ArgoCD application manifests
│   ├── base/                 # Base Kubernetes manifests
│   └── overlays/             # Environment-specific overrides
├── infrastructure/
│   ├── redis/                # Redis deployment
│   └── argocd/               # ArgoCD configuration
├── monitoring/
│   ├── prometheus/           # Prometheus config
│   └── grafana/              # Grafana config
└── scripts/
    ├── setup-cluster.sh      # Create kind cluster
    ├── install-argocd.sh     # Install ArgoCD
    ├── build.sh              # Build container images
    ├── deploy.sh             # Deploy applications
    ├── introduce-drift.sh   # Create drift for debugging
    ├── test-api.sh           # Test API endpoints
    └── cleanup.sh            # Cleanup cluster
```

## Key Takeaways

1. **Drift is inevitable** - Design systems to detect and handle it gracefully
2. **Observability is critical** - You can't fix what you can't see
3. **Health ≠ Sync** - Pods can be healthy while configuration drifts
4. **Balance automation and control** - Auto-sync vs manual approval depends on environment
5. **Git is source of truth** - All production changes must eventually be committed
6. **Process > Technology** - Clear runbooks prevent drift-causing incidents

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [Kubernetes Audit Logs](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)

---

**Production Insight**: The most successful GitOps implementations treat drift as a signal, not noise. High drift rates indicate process problems—unclear runbooks, slow Git workflows, or missing automation. Fix the process, not just the symptom.
