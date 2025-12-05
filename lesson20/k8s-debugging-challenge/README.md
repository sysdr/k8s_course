# Break-It-Friday: Kubernetes Networking Debugging Challenge

## 🎯 Challenge Overview

Welcome to Break-It-Friday! This system contains **5 intentional networking bugs** that you must find and fix. Each bug represents a real-world production issue that has caused outages at major tech companies.

### Your Mission

Deploy this e-commerce system and systematically debug the networking issues preventing it from working correctly.

## 🐛 The Five Bugs (No Peeking!)

1. **Ingress Routing**: Service name misconfiguration
2. **Service Discovery**: Label selector mismatch
3. **NetworkPolicy**: Overly restrictive egress rules
4. **Istio VirtualService**: Routing to non-existent subset
5. **Service Mesh**: Missing DestinationRule subset definition

## 🏗️ System Architecture

```
Internet → Ingress → Frontend Service → Frontend Pods
                        ↓
                  Backend Service → Backend Pods
                        ↓
                  Database Service → PostgreSQL
```

Plus Istio service mesh for advanced traffic management.

## 📋 Prerequisites

- Kubernetes cluster (kind, minikube, or cloud)
- kubectl configured
- Docker
- Istio installed (optional but recommended)
- Ingress controller (nginx)

## 🚀 Quick Start

### 1. Build Images

```bash
cd k8s-debugging-challenge
./scripts/build.sh
```

### 2. Deploy System (with bugs)

```bash
./scripts/deploy.sh
```

### 3. Start Debugging

```bash
./scripts/debug-helper.sh
```

## 🔍 Debugging Methodology: The Five-Minute Drill

Follow this systematic approach used by Netflix SREs:

### Layer 1: Ingress (External → Internal)

```bash
# Check Ingress exists and rules
kubectl get ingress -n debugging-challenge
kubectl describe ingress ecommerce-ingress -n debugging-challenge

# Look for: Backend service name - is it spelled correctly?
```

### Layer 2: Service Discovery (Service → Pods)

```bash
# Check if services have endpoints
kubectl get endpoints -n debugging-challenge

# If endpoints are empty, check label selectors
kubectl get svc frontend-service -n debugging-challenge -o yaml | grep -A3 selector
kubectl get pods -n debugging-challenge --show-labels | grep frontend
```

### Layer 3: NetworkPolicy (Pod → Pod Communication)

```bash
# List all NetworkPolicies
kubectl get networkpolicies -n debugging-challenge

# Check specific policy details
kubectl describe networkpolicy backend-netpol -n debugging-challenge

# Verify egress rules allow backend → database traffic
```

### Layer 4: Service Mesh (Istio Traffic Routing)

```bash
# Check VirtualService configuration
kubectl get virtualservices -n debugging-challenge
kubectl describe virtualservice backend-vs -n debugging-challenge

# Check DestinationRule subsets
kubectl get destinationrules -n debugging-challenge
kubectl describe destinationrule backend-dr -n debugging-challenge

# Verify subset names match between VirtualService and DestinationRule
```

### Layer 5: DNS Resolution

```bash
# Test DNS from within a pod
kubectl exec -it -n debugging-challenge <pod-name> -- nslookup frontend-service
kubectl exec -it -n debugging-challenge <pod-name> -- nslookup backend-service
```

## 🛠️ Debugging Tools

### Essential Commands

```bash
# View pod logs
kubectl logs -n debugging-challenge <pod-name>

# Describe pod (see events)
kubectl describe pod -n debugging-challenge <pod-name>

# Execute commands in pod
kubectl exec -it -n debugging-challenge <pod-name> -- /bin/sh

# Test connectivity
kubectl run curl --rm -it --image=curlimages/curl -n debugging-challenge -- \
  curl http://backend-service:8080/health

# Istio analysis
istioctl analyze -n debugging-challenge

# Check Envoy proxy config
istioctl proxy-config routes <pod-name> -n debugging-challenge
```

### Debug Helper Script

```bash
./scripts/debug-helper.sh
```

This shows:
- Pod status
- Service endpoints
- Ingress configuration
- NetworkPolicies
- Istio configurations

## ✅ How to Verify Fixes

### 1. Check Pod Health

```bash
kubectl get pods -n debugging-challenge
# All pods should be Running with READY 2/2 (with Istio sidecar)
```

### 2. Verify Service Endpoints

```bash
kubectl get endpoints -n debugging-challenge
# All services should have IP addresses listed
```

### 3. Test Internal Connectivity

```bash
kubectl run test --rm -it --image=curlimages/curl -n debugging-challenge -- \
  curl http://frontend-service
```

### 4. Test Ingress Access

```bash
# Add to /etc/hosts: <ingress-ip> ecommerce.local
curl http://ecommerce.local
```

## 🎓 Learning Objectives

After completing this challenge, you should be able to:

- Systematically debug Kubernetes networking issues
- Understand the five-layer networking model
- Use kubectl effectively for troubleshooting
- Identify common misconfigurations
- Debug Istio service mesh issues
- Apply production debugging methodologies

## 📚 Bug Hints (Use Only If Stuck)

<details>
<summary>Hint for Bug #1 (Ingress)</summary>

Check the service name in the Ingress rule. Compare it to the actual Service name. Look for typos.

```bash
kubectl describe ingress ecommerce-ingress -n debugging-challenge | grep -A5 Backend
kubectl get svc -n debugging-challenge
```
</details>

<details>
<summary>Hint for Bug #2 (Service Selector)</summary>

Check if the Service selector labels match the Pod labels exactly.

```bash
kubectl get svc frontend-service -n debugging-challenge -o yaml | grep -A5 selector
kubectl get pods -n debugging-challenge --show-labels
```
</details>

<details>
<summary>Hint for Bug #3 (NetworkPolicy)</summary>

The backend can't reach the database. Check the NetworkPolicy egress rules.

```bash
kubectl describe networkpolicy backend-netpol -n debugging-challenge
# Look for egress rules - is there one allowing traffic to database on port 5432?
```
</details>

<details>
<summary>Hint for Bug #4 (Istio VirtualService)</summary>

The VirtualService routes traffic to a subset that doesn't exist.

```bash
kubectl describe virtualservice backend-vs -n debugging-challenge
kubectl describe destinationrule backend-dr -n debugging-challenge
# Compare subset names
```
</details>

<details>
<summary>Hint for Bug #5 (Istio DestinationRule)</summary>

The DestinationRule is missing a subset definition that the VirtualService references.

```bash
kubectl get destinationrule backend-dr -n debugging-challenge -o yaml
# Check which subsets are defined vs. which are referenced in VirtualService
```
</details>

## 🧹 Cleanup

```bash
./scripts/cleanup.sh
```

## 📖 Additional Resources

- [Kubernetes Networking Guide](https://kubernetes.io/docs/concepts/services-networking/)
- [NetworkPolicy Tutorial](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Istio Traffic Management](https://istio.io/latest/docs/concepts/traffic-management/)
- [Debugging Kubernetes Services](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/)

## 🏆 Bonus Challenges

1. Add monitoring with Prometheus and Grafana
2. Implement circuit breakers with Istio
3. Create additional NetworkPolicies for defense-in-depth
4. Set up distributed tracing with Jaeger
5. Implement rate limiting at the Ingress level

---

**Remember**: Production debugging is about systematic methodology, not guessing. Build your mental model, then verify layer by layer.

Good luck! 🚀
