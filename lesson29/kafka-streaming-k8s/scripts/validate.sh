#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Validating Kafka Pipeline Structure ==="
echo ""

ERRORS=0
WARNINGS=0

# Check required directories
echo "Checking directories..."
REQUIRED_DIRS=(
    "services/producer"
    "services/consumer"
    "services/api"
    "frontend/src"
    "frontend/public"
    "k8s/base"
    "k8s/kafka"
    "k8s/zookeeper"
    "k8s/services"
    "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "${PROJECT_ROOT}/${dir}" ]; then
        echo "  ✓ ${dir}"
    else
        echo "  ✗ ${dir} - MISSING"
        ((ERRORS++))
    fi
done

# Check required files
echo ""
echo "Checking files..."
REQUIRED_FILES=(
    "services/producer/Dockerfile"
    "services/producer/app.py"
    "services/producer/requirements.txt"
    "services/consumer/Dockerfile"
    "services/consumer/app.py"
    "services/consumer/requirements.txt"
    "services/api/Dockerfile"
    "services/api/app.py"
    "services/api/requirements.txt"
    "frontend/Dockerfile"
    "frontend/package.json"
    "frontend/src/App.js"
    "frontend/src/index.js"
    "k8s/base/namespace.yaml"
    "k8s/kafka/statefulset.yaml"
    "k8s/zookeeper/statefulset.yaml"
    "k8s/services/redis.yaml"
    "k8s/services/producer.yaml"
    "k8s/services/consumer.yaml"
    "k8s/services/api.yaml"
    "k8s/services/frontend.yaml"
    "scripts/setup-cluster.sh"
    "scripts/build.sh"
    "scripts/deploy.sh"
    "scripts/demo.sh"
    "scripts/test.sh"
    "scripts/startup.sh"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${file}" ]; then
        echo "  ✓ ${file}"
    else
        echo "  ✗ ${file} - MISSING"
        ((ERRORS++))
    fi
done

# Check scripts are executable
echo ""
echo "Checking script permissions..."
SCRIPTS=(
    "scripts/setup-cluster.sh"
    "scripts/build.sh"
    "scripts/deploy.sh"
    "scripts/demo.sh"
    "scripts/test.sh"
    "scripts/startup.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -x "${PROJECT_ROOT}/${script}" ]; then
        echo "  ✓ ${script} is executable"
    else
        echo "  ✗ ${script} is NOT executable"
        ((WARNINGS++))
    fi
done

# Check for kubectl and docker
echo ""
echo "Checking dependencies..."
if command -v kubectl &> /dev/null; then
    echo "  ✓ kubectl is available"
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null || echo "unknown")
    echo "    Version: ${KUBECTL_VERSION}"
else
    echo "  ✗ kubectl is NOT available"
    echo "    Install kubectl to deploy to Kubernetes"
    ((WARNINGS++))
fi

if command -v docker &> /dev/null; then
    echo "  ✓ docker is available"
    DOCKER_VERSION=$(docker --version 2>/dev/null || echo "unknown")
    echo "    ${DOCKER_VERSION}"
else
    echo "  ✗ docker is NOT available"
    echo "    Install docker to build images"
    ((WARNINGS++))
fi

# Summary
echo ""
echo "=== Validation Summary ==="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✓ All checks passed!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✓ Structure is valid (${WARNINGS} warnings)"
    exit 0
else
    echo "✗ Found ${ERRORS} errors and ${WARNINGS} warnings"
    exit 1
fi
