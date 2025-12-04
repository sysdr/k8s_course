#!/bin/bash
set -euo pipefail

echo "Deploying Network Policy Protected Log Analytics Platform..."

# Create namespaces
echo "Creating namespaces..."
kubectl apply -f k8s/namespaces/namespaces.yaml

# Apply Network Policies first (Zero-Trust approach)
echo "Applying Network Policies..."
kubectl apply -f k8s/network-policies/

# Deploy data layer
echo "Deploying data layer..."
kubectl apply -f k8s/deployments/data-layer/

# Wait for data layer
echo "Waiting for data layer to be ready..."
kubectl wait --for=condition=Ready pods -l app=timescaledb -n data-layer --timeout=300s
echo "Waiting for Kafka (non-blocking)..."
kubectl wait --for=condition=Ready pods -l app=kafka -n data-layer --timeout=60s || echo "⚠️  Kafka not ready, continuing deployment..."

# Deploy backend services
echo "Deploying backend services..."
kubectl apply -f k8s/deployments/backend/

# Wait for backend
echo "Waiting for backend services..."
kubectl wait --for=condition=Ready pods -l app=api-gateway -n backend --timeout=300s

# Deploy frontend
echo "Deploying frontend..."
kubectl apply -f k8s/deployments/frontend/

# Apply autoscaling
echo "Applying autoscaling configs..."
kubectl apply -f k8s/autoscaling/

# Apply Istio configs
echo "Applying Istio service mesh configs..."
kubectl apply -f istio/

# Apply monitoring
echo "Applying monitoring configs..."
kubectl apply -f monitoring/prometheus/

echo "✓ Deployment complete!"
echo ""
echo "Access the application:"
echo "  Dashboard: kubectl port-forward -n frontend svc/dashboard 8080:80"
echo "  Then visit: http://localhost:8080"
echo ""
echo "View Network Policies:"
echo "  kubectl get networkpolicies --all-namespaces"
echo ""
echo "Test connectivity:"
echo "  kubectl exec -it <pod-name> -n <namespace> -- curl <service-url>"
