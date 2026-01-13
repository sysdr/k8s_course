#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying services to Kubernetes..."

# Deploy in order
kubectl apply -f "${PROJECT_ROOT}/k8s/zookeeper/statefulset.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/kafka/statefulset.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/redis.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/producer.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/consumer.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/api.yaml"
kubectl apply -f "${PROJECT_ROOT}/k8s/services/frontend.yaml"

echo "Deployment completed"
