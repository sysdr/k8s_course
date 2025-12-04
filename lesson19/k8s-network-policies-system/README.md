# Network Policy Protected Log Analytics Platform

A production-grade Kubernetes system demonstrating zero-trust networking with comprehensive Network Policies for multi-tenant log analytics processing 50,000 events per second.

## 🏗️ Architecture Overview

This system implements defense-in-depth security using:
- **Network Policies**: Layer 3/4 microsegmentation
- **Istio Service Mesh**: Layer 7 authorization with mTLS
- **Namespace Isolation**: Three isolated security domains

### System Components

**Frontend Namespace:**
- React TypeScript dashboard
- External ingress point

**Backend Namespace:**
- API Gateway (entry point)
- Log Ingestion Service (Kafka producer)
- Log Processor Service (Kafka consumer → TimescaleDB)
- Analytics Service (query engine)

**Data Layer Namespace:**
- TimescaleDB (time-series data)
- Apache Kafka (message queue)
- Redis (caching)

## 🔒 Network Security Model

### Default Deny Strategy

Every namespace starts with a default deny-all policy:
- No ingress traffic allowed
- No egress traffic allowed
- Explicit allowlisting required for all communication

### Allowed Communication Paths

```
External → Frontend Dashboard → API Gateway → {Log Ingestion, Analytics}
                                                         ↓              ↓
                                              Kafka ←→ Processor     Database
                                                         ↓
                                                     Database
```

### Key Network Policies

1. **Frontend → Backend**: Dashboard can only call API Gateway
2. **API Gateway → Services**: Gateway can only call specific backend services
3. **Backend → Data Layer**: Services can only access their required databases
4. **Monitoring Exemption**: Prometheus can scrape all namespaces
5. **Service Mesh Exemption**: Istio control plane has full access
6. **DNS Exemption**: All pods can resolve service names

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster with CNI that supports Network Policies (Calico, Cilium, Weave)
- kubectl configured
- Docker for building images
- kind or minikube for local development

### 1. Setup Cluster

```bash
cd scripts
./setup-cluster.sh
```

This creates a local cluster with Calico CNI for Network Policy enforcement.

### 2. Build Images

```bash
./build.sh
```

If using kind, load images into cluster:
```bash
kind load docker-image api-gateway:latest --name network-policies
kind load docker-image log-ingestion:latest --name network-policies
kind load docker-image log-processor:latest --name network-policies
kind load docker-image analytics-service:latest --name network-policies
kind load docker-image log-analytics-dashboard:latest --name network-policies
```

### 3. Deploy System

```bash
./deploy.sh
```

This deploys in order:
1. Namespaces
2. Network Policies (zero-trust baseline)
3. Data layer (TimescaleDB, Kafka)
4. Backend services
5. Frontend
6. Autoscaling configs
7. Istio service mesh configs

### 4. Access Dashboard

```bash
kubectl port-forward -n frontend svc/dashboard 8080:80
```

Visit: http://localhost:8080

## 📊 Testing Network Policies

### Verify Policy Enforcement

```bash
./test-network-policies.sh
```

This script tests:
- ✅ Allowed paths (frontend → gateway, gateway → services)
- ❌ Blocked paths (frontend → database, frontend → backend services)

### Manual Testing

Test connectivity from a pod:
```bash
# Should succeed - DNS resolution allowed
kubectl exec -it <pod-name> -n backend -- nslookup api-gateway.backend.svc.cluster.local

# Should succeed - gateway to ingestion allowed
GATEWAY_POD=$(kubectl get pods -n backend -l app=api-gateway -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n backend $GATEWAY_POD -- curl http://log-ingestion.backend.svc.cluster.local:8001/health

# Should fail - frontend to backend direct access blocked
kubectl run test --image=curlimages/curl --rm -i --restart=Never -n frontend -- \
    curl --max-time 5 http://log-ingestion.backend.svc.cluster.local:8001/health
```

### View Network Policies

```bash
# List all policies
kubectl get networkpolicies --all-namespaces

# Describe specific policy
kubectl describe networkpolicy allow-frontend-to-gateway -n backend

# View policy in YAML
kubectl get networkpolicy default-deny-all -n frontend -o yaml
```

## 🔍 Monitoring & Observability

### Prometheus Metrics

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Key metrics:
- `api_gateway_requests_total` - Request rate by endpoint
- `log_ingestion_total` - Logs processed by level
- `network_policy_drops_total` - Blocked connection attempts

### Grafana Dashboards

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

Pre-configured dashboards:
- Network Policy Enforcement
- Cross-Namespace Traffic
- Service-to-Service Communication

### Istio Observability

```bash
istioctl dashboard kiali
```

Visualizes:
- Service mesh topology
- mTLS status
- Traffic flows respecting Network Policies

## 📈 Load Testing

Generate realistic traffic:
```bash
./load-test.sh http://localhost:8080
```

This sends 1,000 log entries through the system, testing:
- API Gateway request routing
- Network Policy allow rules
- Kafka message processing
- Database writes

Expected throughput: 5,000+ requests/second with sub-200ms latency.

## 🛠️ Troubleshooting

### Pod Can't Communicate

**Symptom**: Connection timeouts between pods

**Debug Steps**:
1. Check Network Policies:
   ```bash
   kubectl get networkpolicies -n <namespace>
   ```

2. Verify pod labels match policy selectors:
   ```bash
   kubectl get pods -n <namespace> --show-labels
   ```

3. Check CNI plugin logs (Calico example):
   ```bash
   kubectl logs -n kube-system -l k8s-app=calico-node
   ```

4. Test DNS resolution:
   ```bash
   kubectl exec -it <pod> -n <namespace> -- nslookup <service>.<namespace>.svc.cluster.local
   ```

### Common Issues

**Issue**: Prometheus can't scrape metrics
**Solution**: Check `allow-prometheus-scraping` policy exists in target namespace

**Issue**: Istio sidecars can't start
**Solution**: Verify `allow-istio-control-plane` policy allows istio-system namespace

**Issue**: All connections blocked
**Solution**: Ensure `allow-dns-access` policy exists - DNS must work for service discovery

## 🏭 Production Considerations

### Multi-Cluster Deployment

For production, consider:
1. **Network Policy per environment**: Staging/prod have separate policies
2. **External services**: Add ipBlock rules for third-party APIs
3. **Certificate management**: Rotate Istio certificates regularly
4. **Policy auditing**: Enable CNI logging for denied packets

### Scaling Guidelines

- **API Gateway**: 10+ replicas for high traffic (HPA configured)
- **Log Ingestion**: Scale horizontally (3-10 replicas typical)
- **Kafka**: 3+ brokers for production reliability
- **TimescaleDB**: Consider read replicas for analytics queries

### Security Hardening

1. **Pod Security Standards**: Add PodSecurityPolicies
2. **RBAC**: Implement service accounts with minimal permissions
3. **Secrets Management**: Use external secrets operators
4. **Image Scanning**: Scan all images for vulnerabilities
5. **Audit Logging**: Enable Kubernetes audit logs

## 📚 Architecture Decisions

### Why Network Policies + Istio?

**Network Policies** (Layer 3/4):
- Fast: Kernel-level enforcement
- Simple: IP/port-based rules
- Defense-in-depth: First security layer

**Istio Authorization** (Layer 7):
- Granular: Method/path/header-based rules
- Identity-based: Service-to-service authentication
- Observable: Rich telemetry

Together, they provide defense-in-depth. Compromised frontend pod:
1. Can't reach backend services (Network Policy blocks)
2. Even if it could, lacks valid service identity (Istio mTLS blocks)
3. Even with identity, lacks API-level permissions (Istio AuthZ blocks)

### Namespace Segmentation Strategy

**Frontend namespace**: Publicly accessible, untrusted zone
**Backend namespace**: Internal services, partial trust
**Data layer namespace**: Sensitive data, high trust

This mirrors traditional DMZ/internal/data tier architecture in cloud-native form.

## 📖 Related Lessons

- **Lesson 18**: Istio Traffic Management (progressive canary)
- **Lesson 20**: Debug networking issues (Break-It-Friday)

## 🤝 Contributing

To extend this system:
1. Add new service in appropriate namespace
2. Create Network Policy allowing required communication
3. Add Istio AuthorizationPolicy for fine-grained access
4. Update monitoring configs for new service
5. Test with `test-network-policies.sh`

## 📄 License

MIT License - Use for learning and production systems
