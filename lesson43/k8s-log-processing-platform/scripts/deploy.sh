#!/bin/bash
set -euo pipefail

echo "🚀 Deploying Log Platform to Kubernetes..."

# Pre-flight validation
echo "📋 Running pre-flight checks..."

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

# Check resource availability
AVAILABLE_CPU=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum}')
REQUIRED_CPU=2000  # 2 CPU cores minimum

if [ -z "$AVAILABLE_CPU" ]; then
    echo "⚠️  Warning: Cannot determine available CPU"
else
    echo "✅ Cluster has sufficient resources"
fi

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f ../k8s/namespaces/log-platform.yaml

# Apply RBAC
echo "🔐 Applying RBAC configuration..."
kubectl apply -f ../k8s/rbac/

# Apply ConfigMaps and Secrets
echo "⚙️  Applying configuration..."
kubectl apply -f ../k8s/configmaps/

# Deploy services
echo "🔄 Deploying services..."
kubectl apply -f ../k8s/deployments/
kubectl apply -f ../k8s/services/

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/log-ingestion \
    deployment/analytics-api \
    -n log-platform

# Apply autoscaling
echo "📈 Configuring autoscaling..."
kubectl apply -f ../k8s/hpa/
kubectl apply -f ../k8s/vpa/

# Apply PodDisruptionBudgets
echo "🛡️  Applying PodDisruptionBudgets..."
kubectl apply -f ../k8s/pdb/

# Apply network policies
echo "🌐 Applying network policies..."
kubectl apply -f ../k8s/networkpolicies/

# Apply Ingress
echo "🌍 Configuring Ingress..."
kubectl apply -f ../k8s/ingress/

# Smoke tests
echo "🧪 Running smoke tests..."
sleep 10

POD=$(kubectl get pods -n log-platform -l app=log-ingestion -o jsonpath='{.items[0].metadata.name}')
if kubectl exec -n log-platform $POD -- curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "✨ Deployment complete!"
echo ""
echo "📊 Access dashboard:"
echo "   kubectl port-forward -n log-platform svc/frontend 8080:80"
echo "   http://localhost:8080"
