# Project Structure

```
postgres-k8s-production/
├── apps/
│   ├── database-api/              # FastAPI microservice
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py           # API endpoints
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/                  # React dashboard
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── App.js
│   │   │   └── index.js
│   │   ├── public/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── package.json
│   ├── query-service/            # Query analytics service
│   └── analytics-worker/         # Background processing
│
├── k8s/                          # Kubernetes manifests
│   ├── base/
│   │   ├── namespace.yaml        # Namespace definitions
│   │   ├── database/            # PostgreSQL resources
│   │   │   ├── statefulset.yaml # PostgreSQL StatefulSet
│   │   │   ├── service-headless.yaml
│   │   │   ├── service-rw.yaml  # Read-write service
│   │   │   ├── service-ro.yaml  # Read-only service
│   │   │   ├── configmap.yaml   # PostgreSQL config
│   │   │   ├── init-scripts.yaml # Database initialization
│   │   │   ├── secrets.yaml     # Credentials
│   │   │   └── rbac.yaml        # ServiceAccount & RBAC
│   │   ├── pgbouncer/           # Connection pooler
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   ├── services/            # Application services
│   │   │   ├── database-api-deployment.yaml
│   │   │   └── frontend-deployment.yaml
│   │   └── monitoring/          # Monitoring resources
│   └── overlays/
│       ├── dev/                 # Development overrides
│       └── prod/                # Production overrides
│
├── helm/                        # Helm charts
│   └── postgres-ha/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── database/
│           ├── services/
│           ├── monitoring/
│           └── NOTES.txt
│
├── istio/                       # Istio configurations
│   ├── gateway.yaml             # Ingress gateway
│   ├── virtualservice.yaml      # Traffic routing
│   └── destinationrule.yaml     # Load balancing
│
├── monitoring/                  # Observability stack
│   ├── prometheus/
│   │   └── servicemonitor.yaml  # Prometheus scraping
│   └── grafana/
│       └── dashboards/
│           └── postgres-dashboard.json
│
├── scripts/                     # Operational scripts
│   ├── setup-cluster.sh         # Create local cluster
│   ├── build.sh                # Build Docker images
│   ├── deploy.sh               # Deploy to cluster
│   ├── test.sh                 # Run integration tests
│   └── cleanup.sh              # Remove all resources
│
├── backup/                      # Backup utilities
│   └── backup.sh               # PostgreSQL backup script
│
├── tests/                       # Test suites
│
├── docs/                        # Additional documentation
│
├── README.md                    # Main documentation
└── PROJECT_STRUCTURE.md         # This file
```

## Component Overview

### Database Layer
- **PostgreSQL StatefulSet**: 3-replica cluster with streaming replication
- **Headless Service**: Direct pod addressing for replication
- **Read-Write Service**: Routes to primary pod
- **Read-Only Service**: Routes to replica pods
- **PgBouncer**: Connection pooling layer

### Application Layer
- **Database API**: FastAPI service for CRUD operations
- **Frontend**: React dashboard for monitoring
- **Query Service**: Query analytics and optimization
- **Analytics Worker**: Background data processing

### Infrastructure
- **Istio**: Service mesh for traffic management
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards

### Persistent Storage
- **PVCs**: 50Gi per PostgreSQL pod
- **StorageClass**: fast-ssd for high IOPS

## File Counts

- Kubernetes Manifests: 15+
- Docker Images: 4
- Scripts: 5
- Configuration Files: 10+
- Documentation: 3
