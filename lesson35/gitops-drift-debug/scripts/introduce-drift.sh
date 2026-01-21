#!/bin/bash
set -euo pipefail

echo "Introducing drift for debugging exercise..."
echo "==========================================="
echo ""
echo "This script simulates a production incident where an engineer"
echo "manually scales the worker deployment to handle increased load."
echo ""

# Scale worker deployment
echo "Scaling worker deployment from 2 to 8 replicas..."
kubectl scale deployment worker -n production --replicas=8

# Increase memory limit
echo "Increasing worker memory limit from 512Mi to 1Gi..."
kubectl set resources deployment worker -n production --limits=memory=1Gi

echo ""
echo "Drift introduced successfully!"
echo "=============================="
echo ""
echo "The worker deployment now differs from Git:"
echo "  - Replicas: 8 (Git: 2)"
echo "  - Memory: 1Gi (Git: 512Mi)"
echo ""
echo "Check ArgoCD sync status:"
echo "  argocd app get worker"
echo ""
echo "View the diff:"
echo "  argocd app diff worker"
echo ""
echo "Your task: Debug and resolve this drift!"
echo ""
