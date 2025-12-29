#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MISSING_FILES=0

echo "Verifying all expected files are generated..."

# Key files to verify
declare -a REQUIRED_FILES=(
    "k8s/base/namespace.yaml"
    "k8s/base/database/statefulset.yaml"
    "k8s/base/database/service-headless.yaml"
    "k8s/base/database/service-rw.yaml"
    "k8s/base/database/service-ro.yaml"
    "k8s/base/database/configmap.yaml"
    "k8s/base/database/init-scripts.yaml"
    "k8s/base/database/secrets.yaml"
    "k8s/base/database/rbac.yaml"
    "k8s/base/pgbouncer/deployment.yaml"
    "k8s/base/pgbouncer/service.yaml"
    "k8s/base/pgbouncer/configmap.yaml"
    "k8s/base/services/database-api-deployment.yaml"
    "k8s/base/services/frontend-deployment.yaml"
    "apps/database-api/app/main.py"
    "apps/database-api/app/__init__.py"
    "apps/database-api/requirements.txt"
    "apps/database-api/Dockerfile"
    "apps/frontend/src/App.js"
    "apps/frontend/src/index.js"
    "apps/frontend/package.json"
    "apps/frontend/Dockerfile"
    "apps/frontend/nginx.conf"
    "apps/frontend/public/index.html"
    "scripts/setup-cluster.sh"
    "scripts/build.sh"
    "scripts/deploy.sh"
    "scripts/test.sh"
    "scripts/demo.sh"
    "scripts/cleanup.sh"
    "istio/gateway.yaml"
    "istio/virtualservice.yaml"
    "istio/destinationrule.yaml"
    "monitoring/prometheus/servicemonitor.yaml"
    "monitoring/grafana/dashboards/postgres-dashboard.json"
    "README.md"
    "backup/backup.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        echo "ERROR: Missing file: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    echo "✓ All required files are present!"
    exit 0
else
    echo "✗ Found $MISSING_FILES missing file(s)"
    exit 1
fi

