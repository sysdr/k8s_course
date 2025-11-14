# Project Structure

```
k8s-log-analytics/
├── services/                          # Microservices applications
│   ├── log-ingestion/                 # FastAPI log ingestion service
│   │   ├── app/
│   │   │   └── main.py                # FastAPI application
│   │   ├── Dockerfile                 # Multi-stage build
│   │   └── requirements.txt           # Python dependencies
│   ├── analytics-engine/              # Python analytics consumer
│   │   ├── app/
│   │   │   └── main.py                # Kafka consumer + analytics
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── dashboard/                     # React TypeScript frontend
│       ├── src/
│       │   ├── App.tsx                # Main React component
│       │   └── App.css                # Styling
│       ├── Dockerfile                 # Multi-stage build
│       ├── package.json
│       └── nginx.conf                 # Nginx configuration
│
├── k8s/                               # Kubernetes manifests
│   ├── base/                          # Base configurations
│   │   ├── namespace.yaml             # Namespace definition
│   │   ├── log-ingestion-deployment.yaml
│   │   ├── log-ingestion-service.yaml
│   │   ├── analytics-engine-deployment.yaml
│   │   ├── dashboard-deployment.yaml
│   │   ├── hpa.yaml                   # HorizontalPodAutoscaler
│   │   ├── pdb.yaml                   # PodDisruptionBudget
│   │   ├── rbac.yaml                  # RBAC configs
│   │   ├── network-policy.yaml        # NetworkPolicy
│   │   └── secrets.yaml               # Secrets (example)
│   ├── overlays/                      # Kustomize overlays
│   │   ├── dev/                       # Development environment
│   │   └── prod/                      # Production environment
│   ├── monitoring/                    # Monitoring configurations
│   │   ├── servicemonitor.yaml        # Prometheus ServiceMonitor
│   │   ├── prometheus-rules.yaml      # Alerting rules
│   │   └── grafana-dashboard.yaml     # Grafana dashboard
│   └── istio/                         # Istio service mesh
│       ├── gateway.yaml               # Istio Gateway
│       ├── virtualservice.yaml        # VirtualService
│       ├── destinationrule.yaml       # DestinationRule
│       ├── peerauthentication.yaml    # mTLS configuration
│       └── authorizationpolicy.yaml   # Authorization policies
│
├── helm/                              # Helm charts
│   └── log-analytics/
│       ├── Chart.yaml                 # Helm chart metadata
│       ├── values.yaml                # Default values
│       ├── templates/                 # Template files
│       │   ├── deployment.yaml
│       │   └── _helpers.tpl           # Template helpers
│       └── charts/                    # Subchart dependencies
│
├── scripts/                           # Operational scripts
│   ├── setup-cluster.sh               # Create local cluster
│   ├── build.sh                       # Build and load images
│   ├── deploy.sh                      # Deploy platform
│   ├── load-test.sh                   # Run load tests
│   └── cleanup.sh                     # Clean up resources
│
├── docs/                              # Additional documentation
│   ├── ARCHITECTURE.md                # Architecture decisions
│   ├── DEPLOYMENT.md                  # Deployment guide
│   └── TROUBLESHOOTING.md             # Common issues
│
├── README.md                          # Main documentation
└── PROJECT_STRUCTURE.md               # This file
```

## Key Files Description

### Application Code

- **services/log-ingestion/app/main.py**: FastAPI REST API with Kafka producer, health checks, and Prometheus metrics
- **services/analytics-engine/app/main.py**: Kafka consumer with PostgreSQL storage and Redis caching
- **services/dashboard/src/App.tsx**: React dashboard with real-time visualization

### Kubernetes Resources

- **k8s/base/**: Core Kubernetes manifests following production best practices
- **k8s/monitoring/**: Prometheus, Grafana, and alerting configurations
- **k8s/istio/**: Service mesh configuration for security and traffic management

### Deployment Tools

- **helm/log-analytics/**: Helm chart for templated deployments across environments
- **scripts/**: Automation scripts for local development and testing

## Resource Count

- Deployments: 3 (log-ingestion, analytics-engine, dashboard)
- Services: 3 (ClusterIP, LoadBalancer)
- HPA: 1 (log-ingestion)
- PDB: 2 (log-ingestion, analytics-engine)
- NetworkPolicies: 1
- ServiceAccounts: 2
- Istio Resources: 5 (Gateway, VirtualService, DestinationRule, PeerAuth, AuthZ)
- Monitoring: 3 (ServiceMonitor, PrometheusRule, Dashboard)

## Lines of Code

- Python: ~500 lines
- TypeScript/React: ~200 lines
- YAML (K8s): ~800 lines
- Shell scripts: ~300 lines
- Total: ~1,800 lines
