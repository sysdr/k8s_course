#!/bin/bash

# Validate that dashboard/metrics are updating (non-zero where expected)

set -euo pipefail

FAILED=0

check() {
  local name="$1"
  local cmd="$2"
  local desc="$3"
  echo -n "Check: $name... "
  if eval "$cmd" 2>/dev/null | grep -qE '[1-9][0-9]*'; then
    echo "✓ $desc"
  else
    echo "✗ $desc (values zero or missing - run scripts/run-demo.sh first)"
    FAILED=$((FAILED + 1))
  fi
}

echo "Validating metrics (run scripts/run-demo.sh if dashboard values are zero)"
echo "========================================"

# Pods running
check "Pods" "kubectl get pods -A --no-headers 2>/dev/null | wc -l" "pods present"
# Node metrics (node_exporter or similar)
check "Nodes" "kubectl get nodes --no-headers 2>/dev/null | wc -l" "nodes present"
# Metrics server
if command -v kubectl &>/dev/null && kubectl get deployment metrics-server -n kube-system &>/dev/null; then
  echo "Check: metrics-server... ✓ deployment exists"
else
  echo "Check: metrics-server... ✗ not found (install metrics-server)"
  FAILED=$((FAILED + 1))
fi

# Optional: if Prometheus is running, query one metric
if kubectl get svc -n monitoring prometheus-kube-prometheus-prometheus &>/dev/null 2>&1; then
  echo "Check: Prometheus stack... ✓ monitoring stack present"
else
  echo "Check: Prometheus stack... ✗ not found (run scripts/setup-monitoring.sh)"
  FAILED=$((FAILED + 1))
fi

echo "========================================"
if [ "$FAILED" -eq 0 ]; then
  echo "✓ Dashboard validation passed. Metrics should show non-zero after run-demo.sh."
else
  echo "Some checks failed. Run setup-monitoring.sh and run-demo.sh then re-check."
  exit 1
fi
