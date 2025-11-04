# Kubernetes Log Processing System

Production-grade distributed log processing with advanced K8s patterns.

## Quick Start
```bash
./scripts/build.sh          # Build images
./scripts/setup-cluster.sh  # Create cluster
./scripts/deploy.sh         # Deploy system
```

## Architecture
- FastAPI microservices (log ingestion + analytics)
- React dashboard with real-time updates
- Kafka message streaming
- Redis caching
- Istio service mesh (mTLS, circuit breakers)
- Full observability (Prometheus, Grafana, Jaeger)

## Access
```bash
kubectl port-forward -n log-processor svc/dashboard-service 8080:80
kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/jaeger 16686:16686
```

## Key Features
- HPA (3-10 replicas based on load)
- PodDisruptionBudgets for HA
- StatefulSets for Kafka/Redis
- NetworkPolicies for security
- Complete RBAC configuration
