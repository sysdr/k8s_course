# Break-It-Friday: Kubernetes Debugging Challenge

## Overview

This is a deliberately broken multi-tier e-commerce application designed to teach Kubernetes debugging skills. The application consists of:

- **Frontend**: Node.js/Express web server
- **Backend**: Python FastAPI REST API
- **Database**: PostgreSQL with sample product data

## The Challenge

The system has been deployed with **intentional misconfigurations** that cause the frontend to crash in a CrashLoopBackOff state. Your mission is to:

1. Investigate the failure using Kubernetes debugging tools
2. Identify the root cause
3. Apply the appropriate fixes
4. Verify the system is working correctly

## Bugs Included

### Primary Bug: Service Name Mismatch
The frontend is configured to connect to `api-backend:8000`, but the service is named `backend-api`. This is the main issue causing CrashLoopBackOff.

### Secondary Issues
- Potential network policy restrictions
- Configuration mismatches
- Service discovery problems

## Getting Started

### Prerequisites

- Kubernetes cluster (minikube, kind, or any K8s cluster)
- kubectl configured
- Basic understanding of Kubernetes concepts

### Deploy the Broken System

```bash
cd k8s-debug-challenge

# Deploy the broken application
./scripts/deploy-broken.sh

# Check the status (frontend should be failing)
kubectl get pods -n debug-challenge
```

## Debugging Methodology

### Step-by-Step Debugging Guide

Run the interactive debugging guide:

```bash
./scripts/debug-guide.sh
```

This script walks you through the systematic debugging process:

1. **State Assessment**: Review pod status and placement
2. **Event Investigation**: Analyze Kubernetes events
3. **Pod Description**: Examine detailed pod information
4. **Log Analysis**: Review application logs
5. **Service Investigation**: Check service configuration
6. **Connectivity Testing**: Test network connectivity
7. **Solution Identification**: Determine the fix

### Manual Debugging Commands

```bash
# View all pods in the namespace
kubectl get pods -n debug-challenge -o wide

# Check pod events
kubectl get events -n debug-challenge --sort-by='.lastTimestamp'

# Describe a failing pod
kubectl describe pod <frontend-pod-name> -n debug-challenge

# View pod logs
kubectl logs <frontend-pod-name> -n debug-challenge --tail=50

# View previous crash logs
kubectl logs <frontend-pod-name> -n debug-challenge --previous

# List all services
kubectl get svc -n debug-challenge

# Test DNS resolution from within a pod
kubectl exec -n debug-challenge <frontend-pod> -- nslookup backend-api
kubectl exec -n debug-challenge <frontend-pod> -- nslookup api-backend

# Test connectivity
kubectl exec -n debug-challenge <frontend-pod> -- curl http://backend-api:8000/health
```

## Applying Fixes

### Interactive Fix Application

```bash
./scripts/apply-fixes.sh
```

This provides options to:
1. Fix the service name mismatch
2. Update the frontend environment variable
3. Apply network policies
4. Apply all fixes at once

### Manual Fixes

**Option 1: Rename the service**
```bash
kubectl delete svc backend-api -n debug-challenge
kubectl apply -f k8s/fixed/backend.yaml
```

**Option 2: Update frontend environment variable**
```bash
kubectl apply -f k8s/fixed/frontend.yaml
```

**Option 3: Apply both fixes**
```bash
kubectl delete svc backend-api -n debug-challenge
kubectl apply -f k8s/fixed/backend.yaml
kubectl apply -f k8s/fixed/frontend.yaml
```

## Verification

### Verify the Fixes

```bash
./scripts/verify-fix.sh
```

This runs automated tests to confirm:
- All pods are healthy
- Services are communicating correctly
- Data is being retrieved successfully
- External access is working

### Manual Verification

```bash
# Check pod status
kubectl get pods -n debug-challenge

# Verify logs show success
kubectl logs -n debug-challenge -l app=frontend --tail=20

# Port forward to access the application
kubectl port-forward -n debug-challenge svc/frontend-svc 8080:80

# Visit http://localhost:8080 in your browser
```

## Learning Objectives

By completing this challenge, you will learn:

1. **Systematic Debugging**: Follow a structured approach to troubleshooting
2. **Log Analysis**: Extract meaningful information from application logs
3. **Service Discovery**: Understand Kubernetes DNS and service naming
4. **Event Interpretation**: Read and understand Kubernetes events
5. **Connectivity Testing**: Diagnose network issues in a cluster
6. **Configuration Validation**: Verify service selectors and labels
7. **Root Cause Analysis**: Identify the actual problem vs symptoms

## Common Kubernetes Failure Patterns

This challenge demonstrates real-world issues:

1. **Service Name Typos**: Character-level mistakes in configuration
2. **DNS Resolution**: Understanding Kubernetes service DNS
3. **Label Mismatches**: Service selectors not matching pod labels
4. **Network Policies**: Traffic blocking issues
5. **Configuration Drift**: Environment variables not matching infrastructure

## Architecture

```
┌─────────────────┐
│   Frontend      │  ← CrashLoopBackOff (trying to reach api-backend)
│   (Node.js)     │
└────────┬────────┘
         │
         │ Tries: http://api-backend:8000
         │ (DNS fails)
         ↓
┌─────────────────┐
│   Service       │
│   backend-api   │  ← Actual service name
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Backend       │
│   (FastAPI)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │
└─────────────────┘
```

## Project Structure

```
k8s-debug-challenge/
├── k8s/
│   ├── broken/           # Broken manifests for debugging
│   │   ├── namespace.yaml
│   │   ├── postgres.yaml
│   │   ├── backend.yaml
│   │   └── frontend.yaml
│   └── fixed/            # Fixed versions
│       ├── backend.yaml
│       ├── frontend.yaml
│       └── network-policy.yaml
├── scripts/
│   ├── deploy-broken.sh  # Deploy the broken system
│   ├── debug-guide.sh    # Interactive debugging guide
│   ├── apply-fixes.sh    # Apply fixes interactively
│   ├── verify-fix.sh     # Verify the fixes work
│   └── cleanup.sh        # Remove all resources
└── README.md             # This file
```

## Real-World Context

This challenge simulates a production incident where:

- A service was renamed during a deployment
- Configuration wasn't updated to match
- The issue wasn't caught in testing
- Production pods started failing

**Time to Resolution Goals:**
- Beginner: 20-30 minutes
- Intermediate: 10-15 minutes
- Advanced: 5-10 minutes (target for production readiness)

## Additional Challenges

Want to make it harder? Try:

1. **Enable the network policy**: Uncomment the NetworkPolicy in `k8s/broken/network-policy.yaml`
2. **Add label mismatch**: Change the service selector to not match pod labels
3. **Break the backend**: Modify the backend database connection string
4. **Resource constraints**: Add very low resource limits to cause OOMKilled events

## Tips for Success

1. **Read the logs carefully**: The answer is usually in the error messages
2. **Check DNS first**: Many issues are service discovery problems
3. **Verify service selectors**: Labels must match exactly
4. **Use kubectl describe**: Events often contain the smoking gun
5. **Test connectivity**: Use exec to run commands inside pods

## Cleanup

Remove all resources:

```bash
./scripts/cleanup.sh
```

Or manually:

```bash
kubectl delete namespace debug-challenge
```

## Next Steps

After mastering this challenge:

1. Try the additional challenges above
2. Create your own broken scenarios
3. Practice with time limits (5-minute MTTR target)
4. Move on to Lesson 16: Ingress Controllers

## Resources

- [Kubernetes Debugging Documentation](https://kubernetes.io/docs/tasks/debug/)
- [Service DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)

## Questions?

Common questions and answers:

**Q: Why is the frontend crashing instead of just showing an error?**
A: The readiness probe fails because the application can't start successfully, causing Kubernetes to repeatedly restart it.

**Q: How would this be prevented in production?**
A: Integration tests, configuration validation, GitOps with proper review processes, and staging environments.

**Q: What if I can't figure it out?**
A: Use `./scripts/debug-guide.sh` for hints, or check the solution in `k8s/fixed/`.

---

**Remember**: The goal isn't just to fix it, but to understand the debugging process. Take your time and follow the systematic approach!
