#!/bin/bash
set -euo pipefail

echo "🚀 Deploying transaction system..."

# Create namespaces
kubectl apply -f k8s/namespace.yaml

# Deploy MinIO for backup storage
echo "📦 Deploying MinIO..."
kubectl apply -f k8s/velero/minio-deployment.yaml

# Wait for MinIO
echo "⏳ Waiting for MinIO..."
kubectl wait --for=condition=ready pod -l app=minio -n minio --timeout=120s

# Create MinIO bucket
echo "🪣 Creating backup bucket..."
kubectl run -n minio mc-client --image=minio/mc --restart=Never --rm -i --command -- sh -c "mc alias set minio http://minio:9000 minio minio123 && mc mb minio/velero-backups || true" || true

# Deploy infrastructure
echo "📦 Deploying infrastructure..."
kubectl apply -f k8s/base/postgres-statefulset.yaml
kubectl apply -f k8s/base/redis-deployment.yaml

# Wait for infrastructure
echo "⏳ Waiting for infrastructure..."
kubectl wait --for=condition=ready pod -l app=postgres -n transaction-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n transaction-system --timeout=60s

# Deploy application
echo "📦 Deploying application..."
kubectl apply -f k8s/base/rbac.yaml
kubectl apply -f k8s/base/backend-deployment.yaml
kubectl apply -f k8s/base/frontend-deployment.yaml
kubectl apply -f k8s/base/network-policy.yaml

# Wait for application
echo "⏳ Waiting for application..."
kubectl wait --for=condition=ready pod -l app=transaction-api -n transaction-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=transaction-frontend -n transaction-system --timeout=60s || true

# Deploy Istio configuration
echo "📦 Deploying Istio configuration..."
kubectl apply -f k8s/istio/ || echo "⚠️ Istio CRDs not installed, skipping Istio configuration"

# Deploy monitoring
echo "📦 Deploying monitoring..."
kubectl apply -f k8s/monitoring/

# Deploy Velero configuration
echo "📦 Deploying Velero configuration..."
kubectl apply -f k8s/velero/install-velero.yaml || echo "⚠️ Velero deployment failed"
kubectl apply -f k8s/velero/backup-schedule.yaml || echo "⚠️ Backup schedule failed"

echo "✅ Deployment complete!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost (or port-forward)"
echo "  kubectl port-forward -n transaction-system svc/transaction-frontend 8080:80"
echo ""
echo "Access monitoring:"
echo "  Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "  Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo ""
echo "Check Velero status:"
echo "  velero backup get"
