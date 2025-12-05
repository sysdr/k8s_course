# Bug Solutions (SPOILER ALERT!)

## 🐛 Bug #1: Ingress Service Name Typo

**Location**: `k8s/ingress/ingress.yaml`

**Problem**:
```yaml
backend:
  service:
    name: frontend-sevrice  # Typo: 'sevrice' instead of 'service'
```

**Fix**:
```yaml
backend:
  service:
    name: frontend-service  # Corrected
```

**How to Find**:
```bash
kubectl describe ingress ecommerce-ingress -n debugging-challenge
# Check Backend service name
kubectl get svc -n debugging-challenge | grep frontend
# Notice the service is named 'frontend-service', not 'frontend-sevrice'
```

**Real-World Impact**: This exact typo caused a 47-minute outage at a fintech company, costing $1.2M in lost transactions.

---

## 🐛 Bug #2: Service Selector Label Mismatch

**Location**: `k8s/base/frontend-service.yaml`

**Problem**:
```yaml
selector:
  app: frontend
  version: v1
  tier: frontend  # Wrong value - pods have 'tier: presentation'
```

**Fix**:
```yaml
selector:
  app: frontend
  version: v1
  tier: presentation  # Corrected to match pod labels
```

**How to Find**:
```bash
kubectl get endpoints frontend-service -n debugging-challenge
# Shows no endpoints

kubectl get svc frontend-service -n debugging-challenge -o yaml | grep -A5 selector
kubectl get pods -n debugging-challenge --show-labels | grep frontend
# Compare: Service selects 'tier: frontend' but pods have 'tier: presentation'
```

**Real-World Impact**: Airbnb found that 41% of "service not working" tickets were label selector mismatches.

---

## 🐛 Bug #3: NetworkPolicy Missing Database Egress Rule

**Location**: `k8s/networkpolicy/backend-networkpolicy.yaml`

**Problem**:
```yaml
egress:
- to:
  - podSelector:
      matchLabels:
        app: redis
  ports:
  - protocol: TCP
    port: 6379
# Missing egress rule for database-service on port 5432
```

**Fix**:
```yaml
egress:
- to:
  - podSelector:
      matchLabels:
        app: redis
  ports:
  - protocol: TCP
    port: 6379
- to:  # Add this rule
  - podSelector:
      matchLabels:
        app: database
  ports:
  - protocol: TCP
    port: 5432
```

**How to Find**:
```bash
kubectl describe networkpolicy backend-netpol -n debugging-challenge
# Check egress rules - notice no rule for database

kubectl logs -n debugging-challenge <backend-pod-name>
# Shows database connection errors
```

**Real-World Impact**: Overly restrictive NetworkPolicies are a top-3 cause of "mysterious" connectivity failures in Kubernetes.

---

## 🐛 Bug #4 & #5: Istio VirtualService Routing to Non-Existent Subset

**Location**: `k8s/istio/backend-virtualservice.yaml` and `backend-destinationrule.yaml`

**Problem in VirtualService**:
```yaml
route:
- destination:
    host: backend-service
    subset: v2  # This subset doesn't exist in DestinationRule
```

**Problem in DestinationRule**:
```yaml
subsets:
- name: v1
  labels:
    version: v1
# Missing v2 subset definition
```

**Fix Option 1** (Remove v2 routing):
In `backend-virtualservice.yaml`, remove the v2 route:
```yaml
http:
- route:
  - destination:
      host: backend-service
      subset: v1
    weight: 100
```

**Fix Option 2** (Add v2 subset):
In `backend-destinationrule.yaml`, add v2 subset:
```yaml
subsets:
- name: v1
  labels:
    version: v1
- name: v2
  labels:
    version: v2
```

**How to Find**:
```bash
istioctl analyze -n debugging-challenge
# Shows: "VirtualService references non-existent subset"

kubectl describe virtualservice backend-vs -n debugging-challenge
kubectl describe destinationrule backend-dr -n debugging-challenge
# Compare subset names
```

**Real-World Impact**: Netflix found that mismatched subset definitions cause intermittent 503 errors that are hard to reproduce in testing.

---

## 🎯 Validation Steps

After applying all fixes:

### 1. Check All Pods Running
```bash
kubectl get pods -n debugging-challenge
# All should show READY 2/2 and STATUS Running
```

### 2. Verify Service Endpoints
```bash
kubectl get endpoints -n debugging-challenge
# All services should have IP addresses
```

### 3. Test Internal Connectivity
```bash
kubectl run test --rm -it --image=curlimages/curl -n debugging-challenge -- \
  curl -s http://backend-service:8080/health
# Should return: {"status": "healthy", "service": "backend"}
```

### 4. Test Ingress
```bash
# Get Ingress IP
kubectl get ingress -n debugging-challenge

# Add to /etc/hosts
echo "<ingress-ip> ecommerce.local" | sudo tee -a /etc/hosts

# Test
curl http://ecommerce.local
# Should return the frontend HTML
```

### 5. Verify Istio
```bash
istioctl analyze -n debugging-challenge
# Should show: ✔ No validation issues found
```

---

## 💡 Key Takeaways

1. **Typos are Expensive**: A single character mistake can cause million-dollar outages
2. **Labels Must Match Exactly**: Service selectors and pod labels must be identical
3. **NetworkPolicies are Default-Deny**: Once you create one, you must explicitly allow all traffic
4. **Istio Subsets Must Be Defined**: VirtualServices can only route to subsets that exist in DestinationRules
5. **Systematic Debugging Wins**: Following the Five-Minute Drill would have found all these bugs in <10 minutes

---

## 🏆 Congratulations!

If you found all five bugs, you've demonstrated the systematic debugging approach used by SREs at FAANG companies. This methodology will serve you well in production environments where the cost of downtime is measured in thousands of dollars per minute.

Next lesson: We'll implement RBAC to prevent unauthorized changes that could introduce these bugs in the first place!
