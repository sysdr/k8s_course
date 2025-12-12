#!/bin/bash
set -euo pipefail

# Verification script to check all files are generated

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "Verifying Generated Files"
echo "=========================================="
echo ""

ERRORS=0

check_file() {
    local file=$1
    local desc=$2
    
    if [[ -f "${PROJECT_DIR}/${file}" ]]; then
        echo "✓ ${desc}"
        return 0
    else
        echo "✗ ${desc} - MISSING: ${file}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "Checking service files..."
check_file "services/log-ingestion/app.py" "Log Ingestion Service"
check_file "services/log-ingestion/requirements.txt" "Log Ingestion Requirements"
check_file "services/log-ingestion/Dockerfile" "Log Ingestion Dockerfile"

check_file "services/log-processor/app.py" "Log Processor Service"
check_file "services/log-processor/requirements.txt" "Log Processor Requirements"
check_file "services/log-processor/Dockerfile" "Log Processor Dockerfile"

check_file "services/log-query/app.py" "Log Query Service"
check_file "services/log-query/requirements.txt" "Log Query Requirements"
check_file "services/log-query/Dockerfile" "Log Query Dockerfile"

echo ""
echo "Checking frontend files..."
check_file "frontend/security-dashboard/package.json" "Dashboard package.json"
check_file "frontend/security-dashboard/src/App.js" "Dashboard App.js"
check_file "frontend/security-dashboard/src/index.js" "Dashboard index.js"
check_file "frontend/security-dashboard/public/index.html" "Dashboard index.html"
check_file "frontend/security-dashboard/Dockerfile" "Dashboard Dockerfile"

echo ""
echo "Checking Kubernetes manifests..."
check_file "kubernetes/namespaces/logs-public.yaml" "Public namespace"
check_file "kubernetes/namespaces/logs-payment.yaml" "Payment namespace"
check_file "kubernetes/namespaces/logs-system.yaml" "System namespace"
check_file "kubernetes/logs-public/log-ingestion-deployment.yaml" "Ingestion deployment"
check_file "kubernetes/logs-payment/log-processor-deployment.yaml" "Processor deployment"
check_file "kubernetes/logs-public/log-query-deployment.yaml" "Query deployment"
check_file "kubernetes/logs-public/security-dashboard-deployment.yaml" "Dashboard deployment"

echo ""
echo "Checking scripts..."
check_file "scripts/build.sh" "Build script"
check_file "scripts/deploy.sh" "Deploy script"
check_file "scripts/startup.sh" "Startup script"
check_file "scripts/demo.sh" "Demo script"
check_file "scripts/test-security.sh" "Test security script"

echo ""
echo "Checking documentation..."
check_file "README.md" "README"

echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo "=========================================="
    echo "✓ All files verified successfully!"
    echo "=========================================="
    exit 0
else
    echo "=========================================="
    echo "✗ Found $ERRORS missing file(s)"
    echo "=========================================="
    exit 1
fi

