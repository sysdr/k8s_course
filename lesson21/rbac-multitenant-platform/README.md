# RBAC Multi-Tenant Analytics Platform

## Overview

Production-grade multi-tenant Kubernetes platform demonstrating Role-Based Access Control (RBAC) patterns at scale. This system implements a comprehensive RBAC architecture with:

- **4 isolated namespaces** for different teams (Analytics, DevOps, Developers, Auditors)
- **7 ServiceAccounts** with granular permissions
- **4 microservices** (Python FastAPI) demonstrating different permission levels
- **Real-time React dashboard** for RBAC visualization and validation
- **Complete monitoring stack** with Prometheus and Grafana
- **NetworkPolicies** for zero-trust networking

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RBAC Multi-Tenant Platform                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Analytics   │  │   DevOps     │  │  Developers   │          │
│  │  Namespace   │  │  Namespace   │  │  Namespace    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │           RBAC Authorization Layer               │          │
│  │  • Roles          • RoleBindings                 │          │
│  │  • ClusterRoles   • ClusterRoleBindings         │          │
│  └──────────────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────┐           │
│  │              Kubernetes API Server              │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### RBAC Implementation

**ServiceAccounts & Permissions:**
- `log-processor-sa`: Read pods and pod logs in analytics namespace
- `analytics-api-sa`: Cluster-wide read access to analytics resources
- `audit-service-sa`: Read events in analytics namespace
- `rbac-validator-sa`: Create SelfSubjectAccessReviews (validation)
- `devops-team-sa`: Broad deployment permissions across namespaces
- `developer-team-sa`: Read-only access to application resources
- `auditor-sa`: Cluster-wide read-only access for compliance

### Microservices

1. **Log Processor** (Port 8000)
   - Fetches pod logs using Kubernetes API
   - Validates RBAC permissions before operations
   - Demonstrates namespace-scoped permissions

2. **Analytics API** (Port 8001)
   - Aggregates cluster analytics across namespaces
   - Cluster-wide read permissions via ClusterRole
   - RBAC summary and reporting

3. **Audit Service** (Port 8002)
   - Tracks RBAC-related Kubernetes events
   - Permission denial monitoring
   - Compliance reporting

4. **RBAC Validator** (Port 8003)
   - Real-time permission validation
   - Bulk permission checks
   - Uses SelfSubjectAccessReview API

### Frontend Dashboard

React-based dashboard with three main views:
- **RBAC Dashboard**: View roles, bindings, and current permissions
- **Namespace Analytics**: Resource distribution across namespaces
- **Permission Validator**: Test specific RBAC permissions in real-time

## Prerequisites

- Docker (for building images)
- kind (for local Kubernetes cluster)
- kubectl (for cluster management)
- Node.js 18+ (for frontend development)

## Quick Start

### 1. Build All Images

```bash
cd rbac-multitenant-platform
./scripts/build.sh
```

This builds all Docker images:
- log-processor:latest
- analytics-api:latest
- audit-service:latest
- rbac-validator:latest
- rbac-frontend:latest

### 2. Setup Local Kubernetes Cluster

```bash
./scripts/setup-cluster.sh
```

Creates a kind cluster with:
- 1 control plane node
- 2 worker nodes
- All images loaded

### 3. Deploy Platform

```bash
./scripts/deploy.sh
```

Deploys:
- 4 namespaces (analytics, devops, developers, auditors)
- 7 ServiceAccounts
- RBAC policies (Roles, ClusterRoles, Bindings)
- 5 deployments (4 services + frontend)
- Services and NetworkPolicies

### 4. Access Dashboard

```bash
kubectl port-forward -n analytics svc/frontend 8080:80
```

Open browser: http://localhost:8080

## Testing RBAC Permissions

### Automated Tests

```bash
./scripts/test-rbac.sh
```

Tests permissions for all ServiceAccounts across different resources and verbs.

### Manual Testing with kubectl

Test if a ServiceAccount can perform an action:

```bash
# Can log-processor read pods?
kubectl auth can-i get pods \
  --as=system:serviceaccount:analytics:log-processor-sa \
  -n analytics

# Can developer delete pods?
kubectl auth can-i delete pods \
  --as=system:serviceaccount:developers:developer-team-sa \
  -n developers

# List all permissions for a ServiceAccount
kubectl auth can-i --list \
  --as=system:serviceaccount:analytics:analytics-api-sa \
  -n analytics
```

### Using RBAC Validator API

```bash
# Validate a specific permission
curl -X POST http://localhost:8003/api/rbac/validate \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "analytics",
    "resource": "pods",
    "verb": "get"
  }'

# List all permissions
curl http://localhost:8003/api/rbac/list-permissions?namespace=analytics
```

## RBAC Architecture Details

### Roles vs ClusterRoles

**Roles** (namespace-scoped):
- `pod-log-reader`: Read pods and logs in analytics
- `analytics-reader`: Read analytics resources
- `event-reader`: Read events
- `developer-readonly`: Read-only access for developers

**ClusterRoles** (cluster-wide):
- `rbac-validator`: Create access reviews
- `analytics-cluster-reader`: Read resources cluster-wide
- `devops-team-role`: Broad deployment permissions
- `auditor-role`: Read-only compliance access

### Bindings

**RoleBindings** (namespace-scoped permissions):
- Bind ServiceAccounts to Roles within specific namespaces
- Used for most application-level permissions

**ClusterRoleBindings** (cluster-wide permissions):
- Grant cluster-wide access
- Used sparingly for infrastructure services
- Example: Analytics API needs cluster-wide read access

### Permission Matrix

| ServiceAccount | Namespace | Pods | Logs | Secrets | Events | Cluster-wide |
|---------------|-----------|------|------|---------|--------|--------------|
| log-processor-sa | analytics | R | R | - | - | No |
| analytics-api-sa | all | R | - | - | - | Yes (read) |
| audit-service-sa | analytics | - | - | - | R | No |
| rbac-validator-sa | all | - | - | - | - | Yes (validate) |
| devops-team-sa | all | CRUD | R | R | R | Yes |
| developer-team-sa | developers | R | R | - | - | No |
| auditor-sa | all | R | - | - | R | Yes (read) |

Legend: R=Read, C=Create, U=Update, D=Delete

## Monitoring & Observability

### Prometheus Metrics

Service metrics exposed at `/metrics`:
- RBAC permission checks
- API request rates
- Resource access patterns

### Grafana Dashboards

Access Grafana (after deploying monitoring):
```bash
kubectl port-forward -n analytics svc/grafana 3000:3000
```

Default credentials: admin/admin

Dashboards include:
- RBAC permission usage
- ServiceAccount activity
- Namespace resource distribution

## Security Best Practices Demonstrated

1. **Least Privilege Principle**: Each ServiceAccount has minimum required permissions
2. **Namespace Isolation**: Teams isolated in separate namespaces
3. **NetworkPolicies**: Zero-trust networking between services
4. **No Default ServiceAccount**: All pods use explicit ServiceAccounts
5. **Audit Logging**: Track permission checks and denials
6. **Regular Validation**: Automated permission testing
7. **Break-glass Access**: Emergency access patterns for incidents

## Production Considerations

### Scaling

- **Horizontal**: Add replicas to any service
- **Multi-cluster**: Deploy across multiple clusters with federated RBAC
- **Multi-region**: Use ClusterRoles for consistency across regions

### Permission Management

- Use GitOps (ArgoCD/Flux) for RBAC policy management
- Implement quarterly permission audits
- Automate removal of unused permissions
- Version control all RBAC manifests

### Compliance

- Enable Kubernetes audit logging
- Export RBAC events to SIEM
- Implement automated compliance checks
- Document permission rationale

## Troubleshooting

### Pod Can't Access Resources

1. Check ServiceAccount exists:
```bash
kubectl get sa -n analytics
```

2. Verify RoleBinding:
```bash
kubectl get rolebinding -n analytics -o yaml
```

3. Test permission:
```bash
kubectl auth can-i <verb> <resource> \
  --as=system:serviceaccount:<namespace>:<sa-name> \
  -n <namespace>
```

### Permission Denied Errors

- Check if Role/ClusterRole exists and has required rules
- Verify RoleBinding/ClusterRoleBinding links SA to Role
- Ensure namespace is correct (Roles are namespace-scoped)
- Check if ClusterRoleBinding is needed for cluster-wide access

### Services Can't Communicate

- Verify NetworkPolicy allows traffic
- Check service DNS resolution
- Ensure pods are in correct namespace

## Cleanup

Remove all resources:
```bash
./scripts/cleanup.sh
```

Delete kind cluster:
```bash
kind delete cluster --name rbac-platform
```

## Key Learning Outcomes

After completing this lesson, you will understand:

1. **RBAC Fundamentals**
   - ServiceAccounts as pod identities
   - Roles vs ClusterRoles (namespace vs cluster scope)
   - RoleBindings vs ClusterRoleBindings
   - Permission accumulation patterns

2. **Production Patterns**
   - Least privilege access design
   - Multi-tenant namespace isolation
   - Break-glass emergency access
   - Automated permission auditing

3. **Operational Skills**
   - Using `kubectl auth can-i` for permission testing
   - Creating custom Roles for specific use cases
   - Debugging permission denied errors
   - Implementing zero-trust networking with RBAC + NetworkPolicies

4. **Scale Considerations**
   - RBAC policy management at scale
   - Cross-cluster permission consistency
   - Automated compliance and auditing
   - Permission lifecycle management

## Real-World Examples

This platform demonstrates patterns used by:

- **Spotify**: Namespace-per-team isolation with 300+ clusters
- **Netflix**: 94% of ServiceAccounts with namespace-scoped permissions
- **Airbnb**: Admission controllers enforcing explicit ServiceAccounts
- **Uber**: Automated RBAC regression testing with 200+ checks
- **LinkedIn**: Quarterly permission audits removing unused access

## Additional Resources

- [Kubernetes RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [RBAC Best Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
- [Authorization Modes](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
- [Audit Logging](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/)

## License

This is an educational project for Kubernetes RBAC training.
