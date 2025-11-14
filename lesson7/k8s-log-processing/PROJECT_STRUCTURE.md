# Project Structure

Generated: 20251114_070645

```
k8s-log-processing/
├── services/                           # Microservices
│   ├── ingestion-api/                 # FastAPI log ingestion
│   │   ├── app/
│   │   │   └── main.py               # Main application
│   │   ├── tests/
│   │   │   └── test_main.py          # Unit tests
│   │   ├── Dockerfile                # Multi-stage build
│   │   └── requirements.txt          # Python dependencies
│   │
│   ├── analytics-engine/              # Stream processor
│   │   ├── app/
│   │   │   └── main.py               # Consumer application
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.sql
│   │   │   └── run_migrations.sh     # Migration runner
│   │   ├── Dockerfile                # Main container
│   │   ├── Dockerfile.init           # Init container
│   │   └── requirements.txt
│   │
│   └── dashboard/                     # React frontend
│       ├── src/
│       │   ├── components/           # React components
│       │   ├── hooks/
│       │   │   └── useLogMetrics.ts  # Custom hooks
│       │   ├── services/
│       │   │   └── api.ts            # API client
│       │   ├── App.tsx               # Main app
│       │   └── index.tsx             # Entry point
│       ├── public/
│       │   └── index.html
│       ├── Dockerfile                # Multi-stage with nginx
│       ├── nginx.conf                # Nginx configuration
│       ├── package.json
│       └── tsconfig.json
│
├── k8s/                               # Kubernetes manifests
│   ├── base/                         # Base configuration
│   │   ├── namespace.yaml
│   │   ├── redis.yaml
│   │   ├── postgres.yaml            # StatefulSet + PVC
│   │   ├── ingestion-api.yaml       # Deployment + HPA + PDB
│   │   ├── analytics-engine.yaml    # Deployment with init container
│   │   ├── dashboard.yaml           # Deployment
│   │   ├── network-policy.yaml      # Network policies
│   │   └── kustomization.yaml
│   │
│   ├── overlays/                    # Environment-specific
│   │   ├── dev/
│   │   └── prod/
│   │
│   ├── monitoring/                  # Observability stack
│   │   ├── prometheus-config.yaml
│   │   └── grafana.yaml
│   │
│   ├── istio/                       # Service mesh (future)
│   ├── network-policies/            # Security policies
│   └── rbac/                        # RBAC configuration
│       └── serviceaccount.yaml
│
├── helm/                            # Helm charts
│   └── log-processing/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── NOTES.txt
│           ├── ingestion/
│           ├── analytics/
│           └── dashboard/
│
├── scripts/                         # Operational scripts
│   ├── build.sh                    # Build all Docker images
│   ├── deploy.sh                   # Deploy to Kubernetes
│   ├── setup-cluster.sh            # Local kind cluster
│   ├── load-test.sh                # Generate load
│   └── cleanup.sh                  # Cleanup resources
│
├── docker/                         # Docker Compose (local dev)
├── docs/                           # Additional documentation
├── tests/                          # Integration tests
│   ├── integration/
│   └── load/
│
├── README.md                       # Main documentation
└── PROJECT_STRUCTURE.md           # This file

```

## Key Files

### Application Code
- `services/ingestion-api/app/main.py`: FastAPI with health probes, metrics
- `services/analytics-engine/app/main.py`: Redis stream consumer
- `services/dashboard/src/App.tsx`: React dashboard

### Kubernetes Manifests
- `k8s/base/ingestion-api.yaml`: Deployment + HPA + PDB
- `k8s/base/analytics-engine.yaml`: Init container pattern
- `k8s/base/postgres.yaml`: StatefulSet with PVC

### Operational
- `scripts/build.sh`: Build all Docker images
- `scripts/deploy.sh`: Complete deployment orchestration
- `scripts/load-test.sh`: Performance testing

### Documentation
- `README.md`: Complete system documentation
- `helm/log-processing/templates/NOTES.txt`: Post-install instructions

## Component Count

- **Microservices**: 3 (Ingestion API, Analytics Engine, Dashboard)
- **Infrastructure**: 2 (Redis, PostgreSQL)
- **Monitoring**: 2 (Prometheus, Grafana)
- **Kubernetes Deployments**: 5
- **StatefulSets**: 1 (PostgreSQL)
- **Services**: 6
- **ConfigMaps**: 2
- **Secrets**: 1
- **HPA**: 1
- **PDB**: 1
- **Network Policies**: 2

## Pod Patterns Demonstrated

1. **Single Container Pod**: Ingestion API, Redis
2. **Init Container Pattern**: Analytics Engine (DB migrations)
3. **Sidecar Pattern**: Dashboard (React + Nginx)
4. **Multi-Container Pod**: Analytics Engine (init + main)

## Next Steps

1. Build images: `./scripts/build.sh`
2. Setup cluster: `./scripts/setup-cluster.sh`
3. Deploy system: `./scripts/deploy.sh`
4. Run load test: `./scripts/load-test.sh`

For detailed instructions, see README.md
