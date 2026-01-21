#!/bin/bash

set -euo pipefail

SERVICES=("api-gateway" "auth-service" "log-processor" "analytics-service" "frontend")
REPORT_DIR="./trivy-reports"

mkdir -p "$REPORT_DIR"

echo "Starting Trivy security scans..."

for service in "${SERVICES[@]}"; do
    echo "Scanning $service..."
    
    # Build image
    if [ "$service" = "frontend" ]; then
        docker build -t "$service:latest" ./frontend
    else
        docker build -t "$service:latest" "./services/$service"
    fi
    
    # Scan for vulnerabilities
    trivy image \
        --severity CRITICAL,HIGH \
        --format json \
        --output "$REPORT_DIR/$service-vulnerabilities.json" \
        "$service:latest"
    
    # Scan for misconfigurations
    trivy config \
        --severity CRITICAL,HIGH \
        --format json \
        --output "$REPORT_DIR/$service-misconfig.json" \
        "./services/$service" || true
    
    # Generate human-readable report
    trivy image \
        --severity CRITICAL,HIGH \
        --format table \
        "$service:latest" | tee "$REPORT_DIR/$service-report.txt"
    
    echo "Scan complete for $service"
    echo "---"
done

echo "All scans complete. Reports saved to $REPORT_DIR"

# Check for critical vulnerabilities
echo "Checking for critical vulnerabilities..."
for report in "$REPORT_DIR"/*-vulnerabilities.json; do
    critical_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$report")
    high_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$report")
    
    service=$(basename "$report" -vulnerabilities.json)
    echo "$service: $critical_count CRITICAL, $high_count HIGH"
    
    if [ "$critical_count" -gt 0 ]; then
        echo "ERROR: Critical vulnerabilities found in $service"
        exit 1
    fi
done

echo "No critical vulnerabilities found"
