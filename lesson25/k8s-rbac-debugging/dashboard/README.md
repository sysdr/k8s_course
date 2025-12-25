# Kubernetes RBAC Debugging Dashboard

A real-time web dashboard for monitoring and visualizing Kubernetes RBAC operations, cluster metrics, and deployment status.

## Features

- **Real-time Metrics**: Auto-refreshes every 5 seconds
- **Cluster Overview**: View nodes, namespaces, and cluster status
- **RBAC Monitoring**: Track ServiceAccounts, Roles, and RoleBindings
- **Permission Matrix**: Visual display of RBAC permissions for the deployer ServiceAccount
- **Deployment Status**: Monitor application deployments and services
- **Job Monitoring**: Track deployment job status and logs
- **Pod Status**: View all pods across namespaces
- **Live Logs**: Real-time logs from deployment jobs

## Prerequisites

- Python 3.11+
- kubectl configured to access your Kubernetes cluster
- Kubernetes cluster running (kind, minikube, or other)

## Quick Start

### Option 1: Run Locally (Recommended)

```bash
./scripts/start-dashboard.sh
```

The dashboard will be available at: http://localhost:8080

### Option 2: Run with Python Directly

```bash
cd dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Option 3: Run as Docker Container

```bash
cd dashboard
docker build -t rbac-dashboard:latest .
docker run -p 8080:8080 \
  -v ~/.kube/config:/root/.kube/config:ro \
  -e KUBECONFIG=/root/.kube/config \
  rbac-dashboard:latest
```

## Dashboard Sections

### Cluster Overview
- Number of nodes and namespaces
- Node details (role, status, CPU, memory)

### RBAC Configuration
- Current RBAC configuration status (broken/fixed/none)
- Count of ServiceAccounts, Roles, and RoleBindings
- Visual indicator of configuration health

### Deployment Jobs
- Status of deployment jobs in ci-cd namespace
- Success/failure counts
- Start and completion times

### Application Deployments
- Deployments in production namespace
- Replica status (ready/desired)
- Associated services

### RBAC Permission Matrix
- Real-time permission checks for deployer ServiceAccount
- Visual indicators for allowed/denied permissions
- Tests create, get, list, update permissions for:
  - Deployments
  - Services
  - ConfigMaps
  - Secrets

### RBAC Resources
- Detailed tables of all ServiceAccounts, Roles, and RoleBindings
- Namespace information
- Rule summaries

### Pod Status
- All pods across ci-cd, production, and staging namespaces
- Pod status, node assignment, restart counts

### Deployment Job Logs
- Real-time logs from the most recent deployment job
- Color-coded log lines (errors, success, info)
- Auto-scrolling to latest logs

## API Endpoints

The dashboard exposes REST API endpoints for programmatic access:

- `GET /api/metrics` - All metrics
- `GET /api/cluster` - Cluster information
- `GET /api/rbac` - RBAC status
- `GET /api/deployments` - Deployment status
- `GET /api/jobs` - Job status
- `GET /api/pods` - Pod status
- `GET /api/permissions` - Permission check results
- `GET /api/logs` - Job logs
- `GET /api/health` - Health check

## Configuration

Environment variables:

- `PORT` - Server port (default: 8080)
- `HOST` - Server host (default: 0.0.0.0)
- `KUBECONFIG` - Path to kubeconfig file (optional)

## Troubleshooting

### Cannot connect to cluster

Ensure kubectl is configured correctly:
```bash
kubectl cluster-info
```

### Permission denied errors

The dashboard needs read access to:
- Nodes
- Namespaces
- ServiceAccounts
- Roles and RoleBindings
- Deployments
- Jobs
- Pods

### Dashboard shows "Connecting..."

- Check that the cluster is accessible
- Verify kubectl can connect: `kubectl get nodes`
- Check browser console for errors

## Architecture

- **Backend**: Flask web server with Kubernetes Python client
- **Frontend**: Vanilla JavaScript with real-time updates
- **Metrics Collection**: Background thread updates metrics every 5 seconds
- **API**: RESTful endpoints for all metrics

## Development

To modify the dashboard:

1. Edit `app.py` for backend changes
2. Edit `templates/dashboard.html` for frontend changes
3. Restart the server to see changes

## License

Part of the Kubernetes RBAC Debugging Lab project.

