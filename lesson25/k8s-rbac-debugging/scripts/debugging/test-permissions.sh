#!/bin/bash

set -euo pipefail

SA="system:serviceaccount:ci-cd:deployer"
NAMESPACE="production"

echo "Testing RBAC permissions for ServiceAccount: ${SA}"
echo "Target namespace: ${NAMESPACE}"
echo ""

# Test deployment permissions
echo "Deployment permissions:"
kubectl auth can-i create deployments --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ create" || echo "  ✗ create"
kubectl auth can-i get deployments --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ get" || echo "  ✗ get"
kubectl auth can-i list deployments --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ list" || echo "  ✗ list"
kubectl auth can-i update deployments --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ update" || echo "  ✗ update"
kubectl auth can-i delete deployments --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ delete" || echo "  ✗ delete"

echo ""
echo "Service permissions:"
kubectl auth can-i create services --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ create" || echo "  ✗ create"
kubectl auth can-i get services --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ get" || echo "  ✗ get"

echo ""
echo "ConfigMap permissions:"
kubectl auth can-i create configmaps --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ create" || echo "  ✗ create"
kubectl auth can-i get configmaps --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ get" || echo "  ✗ get"

echo ""
echo "Secret permissions:"
kubectl auth can-i get secrets --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ get" || echo "  ✗ get"
kubectl auth can-i create secrets --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ create" || echo "  ✗ create"

echo ""
echo "Pod permissions:"
kubectl auth can-i get pods --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ get" || echo "  ✗ get"
kubectl auth can-i list pods --as="${SA}" -n "${NAMESPACE}" && echo "  ✓ list" || echo "  ✗ list"
