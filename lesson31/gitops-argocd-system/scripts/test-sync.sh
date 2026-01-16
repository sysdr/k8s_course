#!/bin/bash
set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Testing GitOps sync workflow..."

# Make a change to the GitOps repo
cd "${PROJECT_ROOT}/gitops-repo/apps/base"

# Update replica count
sed -i 's/replicas: 2/replicas: 3/g' deployment.yaml

echo "Changed replica count to 3"
echo "Commit and push this change to see ArgoCD sync automatically"
echo ""
echo "Run these commands:"
echo "  git add ."
echo "  git commit -m 'Scale up replicas to 3'"
echo "  git push origin main"
echo ""
echo "Then watch ArgoCD sync:"
echo "  kubectl get applications -n argocd -w"
