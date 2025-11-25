# Solution Walkthrough: Debugging the E-Commerce Application

## Problem Overview

The frontend pods are stuck in CrashLoopBackOff because they cannot connect to the backend API service. This document walks through the systematic debugging process and solution.

## Step 1: Initial Observation

```bash
kubectl get pods -n debug-challenge
```

**Expected Output:**
```
NAME                        READY   STATUS             RESTARTS   AGE
backend-xxx                 1/1     Running            0          2m
frontend-xxx                0/1     CrashLoopBackOff   5          2m
postgres-xxx                1/1     Running            0          2m
```

**Key Observations:**
- Backend and PostgreSQL are running fine
- Frontend is in CrashLoopBackOff with multiple restarts
- This suggests an application-level issue, not infrastructure

## Step 2: Check Events

```bash
kubectl get events -n debug-challenge --sort-by='.lastTimestamp' | tail -20
```

**Key Events:**
```
BackOff     pod/frontend-xxx    Back-off restarting failed container
```

This confirms the container is crashing, but doesn't tell us why.

## Step 3: Examine Frontend Logs

```bash
FRONTEND_POD=$(kubectl get pods -n debug-challenge -l app=frontend -o jsonpath='{.items[0].metadata.name}')
kubectl logs $FRONTEND_POD -n debug-challenge --tail=50
```

**Critical Log Entry:**
```
Frontend starting... API_URL: http://api-backend:8000
Configured to connect to backend at: http://api-backend:8000
Failed to fetch products: getaddrinfo ENOTFOUND api-backend
```

**Analysis:**
- The frontend is trying to connect to `api-backend:8000`
- DNS resolution is failing (`ENOTFOUND`)
- This suggests the service name doesn't exist

## Step 4: Investigate Services

```bash
kubectl get svc -n debug-challenge
```

**Output:**
```
NAME           TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
backend-api    ClusterIP      10.96.1.1      <none>        8000/TCP         3m
frontend-svc   LoadBalancer   10.96.1.2      <pending>     80:30080/TCP     3m
postgres-svc   ClusterIP      10.96.1.3      <none>        5432/TCP         3m
```

**Critical Discovery:**
- The service is named `backend-api`
- The frontend is looking for `api-backend`
- This is a service name mismatch!

## Step 5: Verify the Mismatch

Check the frontend environment configuration:

```bash
kubectl get deployment frontend -n debug-challenge -o yaml | grep -A 2 "API_URL"
```

**Output:**
```yaml
- name: API_URL
  value: http://api-backend:8000
```

Confirm the actual service name:

```bash
kubectl get svc backend-api -n debug-challenge
```

**Confirmed:** Service name is `backend-api`, but frontend expects `api-backend`.

## Step 6: Test DNS Resolution

```bash
# Test the wrong name (should fail)
kubectl exec -n debug-challenge $FRONTEND_POD -- nslookup api-backend

# Test the correct name (should work)
kubectl exec -n debug-challenge $FRONTEND_POD -- nslookup backend-api
```

**Results:**
- `api-backend`: DNS resolution fails
- `backend-api`: DNS resolves successfully

This confirms our diagnosis.

## Solution Options

### Option 1: Rename the Service (Recommended)

This approach updates the infrastructure to match the application configuration.

```bash
# Delete the incorrectly named service
kubectl delete svc backend-api -n debug-challenge

# Apply the fixed service with correct name
kubectl apply -f k8s/fixed/backend.yaml
```

**Fixed Service YAML:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-backend  # Changed from backend-api
  namespace: debug-challenge
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: backend  # Selector remains the same
```

### Option 2: Update Frontend Configuration

This approach updates the application to match the existing infrastructure.

```bash
# Apply the fixed frontend deployment
kubectl apply -f k8s/fixed/frontend.yaml
```

**Fixed Frontend Environment:**
```yaml
env:
- name: API_URL
  value: "http://backend-api:8000"  # Changed from api-backend
```

### Which Option to Choose?

**Option 1 (Rename Service):**
- Pro: Fixes at infrastructure level
- Pro: No application restart logic changes
- Con: Might affect other services depending on the backend

**Option 2 (Update Frontend):**
- Pro: Doesn't touch working backend
- Pro: Frontend will restart automatically
- Con: Requires redeployment of application

**For this scenario:** Option 1 is recommended because:
1. The backend service name is clearly wrong
2. No other services depend on it
3. Simpler to fix once at the infrastructure layer

## Step 7: Apply the Fix

```bash
# Option 1: Fix the service name
kubectl delete svc backend-api -n debug-challenge
kubectl apply -f k8s/fixed/backend.yaml

# Wait for frontend pods to stabilize
sleep 10
kubectl get pods -n debug-challenge -l app=frontend -w
```

## Step 8: Verify the Fix

```bash
# Check pod status
kubectl get pods -n debug-challenge

# Check logs for successful connection
kubectl logs -n debug-challenge -l app=frontend --tail=20

# Test from within the frontend pod
kubectl exec -n debug-challenge $FRONTEND_POD -- curl -s http://api-backend:8000/health

# Test end-to-end functionality
kubectl port-forward -n debug-challenge svc/frontend-svc 8080:80
# Visit http://localhost:8080
```

**Success Indicators:**
```bash
# Pods show Running status
NAME                        READY   STATUS    RESTARTS   AGE
frontend-xxx                1/1     Running   0          1m

# Logs show successful backend connection
Frontend starting... API_URL: http://api-backend:8000
Configured to connect to backend at: http://api-backend:8000
Successfully fetched 10 products
```

## Root Cause Analysis

**What Happened:**
1. During deployment, someone created a service named `backend-api`
2. The frontend application was configured to connect to `api-backend`
3. The typo wasn't caught in testing
4. DNS resolution failed because `api-backend` doesn't exist
5. Frontend couldn't start, leading to CrashLoopBackOff

**Why It Wasn't Caught:**
- No integration tests between frontend and backend
- Configuration and infrastructure not validated together
- Deployment pipeline didn't verify service connectivity

## Prevention Strategies

### 1. Integration Testing
```yaml
# test-connectivity.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: integration-test
spec:
  template:
    spec:
      containers:
      - name: test
        image: curlimages/curl
        command:
        - sh
        - -c
        - |
          curl -f http://backend-api:8000/health || exit 1
      restartPolicy: Never
```

### 2. Configuration Validation
Use ConfigMaps with validation:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  BACKEND_SERVICE: "api-backend"
  BACKEND_PORT: "8000"
```

### 3. Helm Values
Use Helm to centralize configuration:

```yaml
# values.yaml
backend:
  serviceName: api-backend
  port: 8000

frontend:
  backendUrl: "http://{{ .Values.backend.serviceName }}:{{ .Values.backend.port }}"
```

### 4. Service Mesh
With Istio, you get automatic service discovery validation and better error messages.

## Key Learnings

1. **Service naming matters**: A single character typo can cause complete failure
2. **DNS is critical**: Most connectivity issues are service discovery problems
3. **Logs tell the story**: The error message clearly indicated DNS failure
4. **Systematic debugging**: Following a methodical approach leads to quick resolution
5. **Prevention is better**: Integration tests would have caught this before deployment

## Time to Resolution

**Target MTTR by Experience Level:**
- Beginner: 20-30 minutes (learning the tools)
- Intermediate: 10-15 minutes (familiar with kubectl)
- Advanced: 5-10 minutes (systematic approach, immediate focus on logs and DNS)

## Next Steps

After mastering this:
1. Try the additional challenges (network policies, label mismatches)
2. Practice with a timer to improve MTTR
3. Create your own broken scenarios
4. Move on to Lesson 16: Ingress Controllers
