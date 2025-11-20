#!/bin/bash
set -euo pipefail

echo "Testing health probes..."

# Get pod names
COLLECTOR_POD=$(kubectl get pod -n log-analytics -l app=log-collector -o jsonpath='{.items[0].metadata.name}')
PROCESSOR_POD=$(kubectl get pod -n log-analytics -l app=log-processor -o jsonpath='{.items[0].metadata.name}')
API_POD=$(kubectl get pod -n log-analytics -l app=analytics-api -o jsonpath='{.items[0].metadata.name}')

echo "Testing Log Collector probes..."
kubectl exec -n log-analytics $COLLECTOR_POD -- curl -s http://localhost:8080/health/live
kubectl exec -n log-analytics $COLLECTOR_POD -- curl -s http://localhost:8080/health/ready
kubectl exec -n log-analytics $COLLECTOR_POD -- curl -s http://localhost:8080/health/startup

echo ""
echo "Testing Log Processor probes..."
kubectl exec -n log-analytics $PROCESSOR_POD -- curl -s http://localhost:8080/health/live
kubectl exec -n log-analytics $PROCESSOR_POD -- curl -s http://localhost:8080/health/ready
kubectl exec -n log-analytics $PROCESSOR_POD -- curl -s http://localhost:8080/health/startup

echo ""
echo "Testing Analytics API probes..."
kubectl exec -n log-analytics $API_POD -- curl -s http://localhost:8080/health/live
kubectl exec -n log-analytics $API_POD -- curl -s http://localhost:8080/health/ready
kubectl exec -n log-analytics $API_POD -- curl -s http://localhost:8080/health/startup

echo ""
echo "All health probe tests complete!"
