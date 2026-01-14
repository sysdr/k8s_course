#!/bin/bash

set -euo pipefail

echo "Deploying all broken scenarios..."

# Deploy Scenario 1
echo "Deploying Scenario 1: PVC Pending..."
kubectl apply -f ../scenarios/01-pvc-pending/postgres-statefulset.yaml

# Deploy Scenario 2
echo "Deploying Scenario 2: Resource Quota..."
kubectl apply -f ../scenarios/02-resource-quota/quota-exhaustion.yaml

# Deploy Scenario 3
echo "Deploying Scenario 3: PostgreSQL CrashLoop..."
kubectl apply -f ../scenarios/03-postgres-crashloop/postgres-broken.yaml

# Deploy Scenario 4
echo "Deploying Scenario 4: Volume Permissions..."
kubectl apply -f ../scenarios/04-volume-permissions/permissions-broken.yaml

# Deploy Scenario 5
echo "Deploying Scenario 5: Redis Anti-Affinity..."
kubectl apply -f ../scenarios/05-redis-antiaffinity/redis-broken.yaml

# Deploy Scenario 6
echo "Deploying Scenario 6: Storage Timeout..."
kubectl apply -f ../scenarios/06-storage-timeout/cassandra-timeout.yaml

echo ""
echo "✓ All scenarios deployed!"
echo ""
echo "Check status with:"
echo "  kubectl get pods -A"
echo "  kubectl get pvc -A"
echo ""
echo "Start debugging!"
