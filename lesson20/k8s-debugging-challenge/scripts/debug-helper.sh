#!/bin/bash

set -euo pipefail

NAMESPACE="debugging-challenge"

echo "🔍 Kubernetes Debugging Helper"
echo "=============================="
echo ""

# Function to check resources
check_resource() {
    local resource=$1
    local name=$2
    echo "Checking ${resource} ${name}..."
    kubectl get ${resource} ${name} -n ${NAMESPACE} 2>/dev/null || echo "  ❌ Not found"
    echo ""
}

# Check pods
echo "📦 Pods Status:"
kubectl get pods -n ${NAMESPACE} -o wide
echo ""

# Check services and endpoints
echo "🔌 Services and Endpoints:"
for svc in $(kubectl get svc -n ${NAMESPACE} -o name 2>/dev/null); do
    svc_name=$(echo $svc | cut -d'/' -f2)
    echo "Service: ${svc_name}"
    kubectl get endpoints ${svc_name} -n ${NAMESPACE}
    echo ""
done

# Check Ingress
echo "🌐 Ingress Configuration:"
kubectl describe ingress -n ${NAMESPACE}
echo ""

# Check NetworkPolicies
echo "🔒 NetworkPolicies:"
kubectl get networkpolicies -n ${NAMESPACE}
echo ""

# Check Istio VirtualServices
echo "🕸️  Istio VirtualServices:"
kubectl get virtualservices -n ${NAMESPACE}
echo ""

# Check Istio DestinationRules
echo "🎯 Istio DestinationRules:"
kubectl get destinationrules -n ${NAMESPACE}
echo ""

echo "💡 Debugging Commands:"
echo "  kubectl logs -n ${NAMESPACE} <pod-name>"
echo "  kubectl describe pod -n ${NAMESPACE} <pod-name>"
echo "  kubectl exec -it -n ${NAMESPACE} <pod-name> -- /bin/sh"
echo "  kubectl get endpoints -n ${NAMESPACE} <service-name>"
echo "  istioctl analyze -n ${NAMESPACE}"
