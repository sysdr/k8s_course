# Project Structure

```
k8s-log-platform/
├── services/
│   ├── log-ingestion/
│   │   ├── app/
│   │   │   └── main.py              # FastAPI application
│   │   ├── tests/
│   │   │   └── test_main.py         # Unit tests
│   │   ├── Dockerfile               # Multi-stage build
│   │   └── requirements.txt
│   └── log-processor/
│       ├── app/
│       │   └── main.py              # Kafka consumer
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Main React component
│   │   ├── services/
│   │   │   └── logService.ts        # API client
│   │   └── components/              # React components
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── *-deployment.yaml        # Deployments
│   │   ├── *-service.yaml           # Services
│   │   ├── *-hpa.yaml               # Autoscaling
│   │   ├── *-vpa.yaml
│   │   ├── pod-disruption-budgets.yaml
│   │   ├── rbac.yaml                # RBAC configuration
│   │   ├── network-policies.yaml    # Network security
│   │   ├── secrets.yaml
│   │   └── ingress.yaml
│   └── overlays/
│       ├── dev/
│       └── prod/
├── helm/
│   └── log-platform/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           └── deployment.yaml
├── istio/
│   ├── gateway.yaml
│   ├── virtual-service.yaml
│   ├── destination-rule.yaml
│   ├── peer-authentication.yaml      # mTLS
│   └── authorization-policy.yaml
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus-config.yaml
│   │   └── prometheus-deployment.yaml
│   ├── grafana/
│   │   ├── grafana-deployment.yaml
│   │   └── dashboards/
│   │       └── kubernetes-dashboard.json
│   ├── jaeger/
│   │   └── jaeger-deployment.yaml
│   └── alertmanager/
├── infrastructure/
│   ├── kafka/
│   │   ├── kafka-deployment.yaml
│   │   └── zookeeper-deployment.yaml
│   ├── postgresql/
│   │   └── postgresql-statefulset.yaml
│   └── redis/
│       └── redis-deployment.yaml
├── scripts/
│   ├── setup-cluster.sh              # Local cluster setup
│   ├── build.sh                      # Build images
│   ├── deploy.sh                     # Deploy to K8s
│   ├── monitoring-setup.sh           # Port forwarding
│   ├── load-test.sh                  # Performance testing
│   └── cleanup.sh                    # Cleanup resources
├── load-tests/
│   ├── locustfile.py                 # Load test scenarios
│   └── load-test-data.json
├── .github/
│   └── workflows/
│       └── ci-cd.yaml                # CI/CD pipeline
├── docs/
├── docker-compose.yml                # Local development
├── README.md                         # Main documentation
└── PROJECT_STRUCTURE.md              # This file
```

## Component Count

- Python Services: 2
- React Application: 1
- Kubernetes Manifests: 20+
- Helm Chart: 1 (with templates)
- Istio Configurations: 5
- Monitoring Components: 3 (Prometheus, Grafana, Jaeger)
- Infrastructure Services: 3 (Kafka, PostgreSQL, Redis)
- Operational Scripts: 6
- CI/CD Pipelines: 1

## Key Files

- `services/log-ingestion/app/main.py`: Core log ingestion logic
- `services/log-processor/app/main.py`: Log processing worker
- `frontend/src/App.tsx`: Dashboard UI
- `k8s/base/*.yaml`: Kubernetes resource definitions
- `istio/*.yaml`: Service mesh configuration
- `monitoring/*/*.yaml`: Observability stack
- `scripts/deploy.sh`: Deployment orchestration
- `README.md`: Complete documentation

## Technologies Used

- **Languages**: Python 3.11, TypeScript, Bash
- **Frameworks**: FastAPI, React 18
- **Orchestration**: Kubernetes 1.28+, Helm 3
- **Service Mesh**: Istio 1.19+
- **Messaging**: Apache Kafka
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Monitoring**: Prometheus, Grafana, Jaeger
- **CI/CD**: GitHub Actions
- **Load Testing**: Locust, Apache Bench

