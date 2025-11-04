#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }

errors=0

log_info "Validating generated files..."

# Check required files exist
required_files=(
    "apps/log-ingestion/main.py"
    "apps/log-ingestion/requirements.txt"
    "apps/log-ingestion/Dockerfile"
    "apps/log-analytics/main.py"
    "apps/log-analytics/requirements.txt"
    "apps/log-analytics/Dockerfile"
    "apps/dashboard/package.json"
    "apps/dashboard/src/App.js"
    "apps/dashboard/Dockerfile"
    "k8s/base/namespace.yaml"
    "k8s/base/redis-deployment.yaml"
    "k8s/base/log-ingestion-deployment.yaml"
    "k8s/base/log-analytics-deployment.yaml"
    "k8s/base/dashboard-deployment.yaml"
    "scripts/startup.sh"
    "scripts/test.sh"
    "scripts/demo.sh"
    "scripts/build.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        log_info "✓ $file exists"
    else
        log_error "✗ $file missing"
        errors=$((errors + 1))
    fi
done

# Check Python syntax
log_info "Validating Python syntax..."
for py_file in apps/log-ingestion/main.py apps/log-analytics/main.py; do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        log_info "✓ $py_file syntax valid"
    else
        log_error "✗ $py_file syntax error"
        errors=$((errors + 1))
    fi
done

# Check YAML syntax
log_info "Validating YAML syntax..."
for yaml_file in k8s/base/*.yaml; do
    if command -v yamllint &>/dev/null; then
        if yamllint "$yaml_file" &>/dev/null; then
            log_info "✓ $yaml_file syntax valid"
        else
            log_warn "⚠ $yaml_file may have issues (yamllint not available or found issues)"
        fi
    else
        # Basic YAML check with Python (handles multi-document YAML)
        if python3 -c "import yaml; list(yaml.safe_load_all(open('$yaml_file')))" 2>/dev/null; then
            log_info "✓ $yaml_file syntax valid"
        else
            log_error "✗ $yaml_file syntax error"
            python3 -c "import yaml; list(yaml.safe_load_all(open('$yaml_file')))" 2>&1 | head -3
            errors=$((errors + 1))
        fi
    fi
done

if [ $errors -eq 0 ]; then
    log_info "All file validations passed!"
    exit 0
else
    log_error "Found $errors validation error(s)"
    exit 1
fi

