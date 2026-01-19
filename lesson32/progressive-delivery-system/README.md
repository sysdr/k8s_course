# Progressive Delivery System

A Kubernetes-based progressive delivery system demonstrating blue-green and canary deployment strategies using Istio and Flagger.

## Prerequisites

Before running this project, ensure you have the following installed:

- **Docker** (version 20.10 or later)
- **kubectl** (Kubernetes command-line tool)
- **Kind** (Kubernetes in Docker) - will be installed automatically if not present
- **curl** (for downloading dependencies)
- **bash** (for running scripts)

## Project Structure

```
progressive-delivery-system/
├── services/              # Backend services (Python FastAPI)
│   ├── order-service/
│   └── payment-gateway/
├── frontend/              # React frontend dashboard
├── k8s/                   # Kubernetes manifests
│   ├── base/             # Base deployments
│   ├── blue-green/       # Blue-green deployment configs
│   ├── canary/           # Canary deployment configs
│   ├── istio/            # Istio service mesh configs
│   └── monitoring/       # Prometheus & Grafana configs
└── scripts/              # Setup and deployment scripts
```

## Quick Start

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd progressive-delivery-system
```

### Step 2: Setup Kubernetes Cluster

Run the setup script to create a Kind cluster and install required components (Istio, Flagger, metrics-server):

```bash
chmod +x scripts/setup-cluster.sh
./scripts/setup-cluster.sh
```

This script will:
- Install Kind if not already installed
- Create a Kind cluster named `progressive-delivery`
- Install Istio service mesh
- Install Flagger for progressive delivery
- Install metrics-server for HPA

**Note:** This may take several minutes to complete.

### Step 3: Build Container Images

Build all Docker images and load them into the Kind cluster:

```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

This will build:
- `order-service:v1` and `order-service:v2` (canary version)
- `payment-gateway:v1`
- `progressive-delivery-frontend:v1`

### Step 4: Deploy the System

Deploy all services, monitoring, and configurations:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

This will:
- Create the `progressive-delivery` namespace
- Deploy base services (order-service, payment-gateway)
- Configure Istio gateway and security policies
- Deploy monitoring stack (Prometheus, Grafana)
- Configure Flagger canary deployments

### Step 5: Verify Deployment

Check that all pods are running:

```bash
kubectl get pods -n progressive-delivery
```

Wait until all pods show `Running` status. This may take a few minutes.

## Accessing the Services

### Order Service
- **URL:** http://localhost/orders
- **Health Check:** http://localhost/orders/health

### Payment Gateway
- **URL:** http://localhost/payments
- **Health Check:** http://localhost/payments/health

### Grafana Dashboard
- **URL:** http://localhost:30300
- Default credentials: `admin/admin` (change on first login)

### Prometheus
Access via port-forward:
```bash
kubectl port-forward -n progressive-delivery svc/prometheus 9090:9090
```
Then open: http://localhost:9090

## Progressive Delivery Features

### Canary Deployment

Monitor canary deployment status:
```bash
kubectl get canary -n progressive-delivery -w
```

Trigger a canary deployment:
```bash
chmod +x scripts/trigger-canary.sh
./scripts/trigger-canary.sh
```

### Blue-Green Deployment

Switch between blue and green environments:
```bash
cd k8s/blue-green
chmod +x blue-green-switch.sh
./blue-green-switch.sh
```

## Monitoring and Load Testing

### Run Load Tests

Generate traffic to test the canary deployment:
```bash
chmod +x scripts/load-test.sh
./scripts/load-test.sh
```

### View Metrics

Access Grafana at http://localhost:30300 to view:
- Request rates
- Error rates
- Latency metrics
- Canary deployment progress

## Troubleshooting

### Check Pod Logs

```bash
# Order service logs
kubectl logs -n progressive-delivery deployment/order-service -f

# Payment gateway logs
kubectl logs -n progressive-delivery deployment/payment-gateway -f
```

### Check Service Status

```bash
kubectl get svc -n progressive-delivery
kubectl get deployments -n progressive-delivery
kubectl get canary -n progressive-delivery
```

### Restart Services

If services are not responding:
```bash
kubectl rollout restart deployment/order-service -n progressive-delivery
kubectl rollout restart deployment/payment-gateway -n progressive-delivery
```

### Clean Up

To delete the entire cluster and start fresh:
```bash
kind delete cluster --name progressive-delivery
```

Then run the setup script again.

## Development

### Local Development (Frontend)

```bash
cd frontend
npm install
npm start
```

Frontend will be available at http://localhost:3000

### Local Development (Services)

```bash
# Order Service
cd services/order-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Payment Gateway
cd services/payment-gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
