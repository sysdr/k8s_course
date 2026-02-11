#!/bin/bash
# Start all port-forwards for observability stack

echo "🚀 Starting port-forwards for observability stack..."
echo ""

# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 > /dev/null 2>&1 &
echo "✅ Grafana:        http://localhost:3000 (admin/admin)"

# Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 > /dev/null 2>&1 &
echo "✅ Prometheus:     http://localhost:9090"

# Alertmanager
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093 > /dev/null 2>&1 &
echo "✅ Alertmanager:   http://localhost:9093"

# Log Processor API
kubectl port-forward svc/log-processor 8000:80 > /dev/null 2>&1 &
echo "✅ Log Processor:  http://localhost:8000"

# Metrics Exporter
kubectl port-forward svc/metrics-exporter 8081:8081 > /dev/null 2>&1 &
echo "✅ Metrics Export: http://localhost:8081"

echo ""
echo "⏳ Waiting 3 seconds for port-forwards to initialize..."
sleep 3

echo ""
echo "📊 Quick Access:"
echo "   Grafana:    http://localhost:3000"
echo "   Prometheus: http://localhost:9090"
echo "   API:        http://localhost:8000"
echo ""
echo "🛑 To stop all port-forwards: pkill -f 'kubectl port-forward'"
