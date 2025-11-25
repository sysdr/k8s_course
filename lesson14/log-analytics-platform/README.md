# Distributed Log Analytics Platform

A production-grade Kubernetes-based log analytics system demonstrating persistent storage patterns, StatefulSets, and data durability at scale.

## Architecture Overview

This system processes 50,000 events per second with complete data persistence across:

- **TimescaleDB** (StatefulSet): Time-series database with persistent volumes for log storage
- **Kafka** (StatefulSet): Message queue with persistent commit logs
- **MinIO** (StatefulSet): S3-compatible object storage for log archival
- **Log Ingester**: FastAPI service for log ingestion (scales 3-10 replicas)
- **Query API**: High-performance log query service with TimescaleDB
- **Aggregator**: Kafka consumer writing logs to TimescaleDB
- **Frontend**: React TypeScript dashboard for log visualization

### Key Kubernetes Patterns Demonstrated

1. **StatefulSets with Persistent Storage**
   - Stable network identities (postgres-0, postgres-1)
   - Ordered deployment and scaling
   - Persistent volumes following pods across rescheduling

2. **Storage Classes and Dynamic Provisioning**
   - Fast SSD storage class for databases
   - Standard HDD storage for object storage
   - Volume binding modes and reclaim policies

3. **Data Durability and Backup**
   - Persistent volume claims with retention policies
   - Volume snapshots for backup
   - Disaster recovery patterns

4. **Resource Management**
   - CPU and memory requests/limits for all pods
   - Horizontal Pod Autoscaling for stateless services
   - Resource quotas at namespace level

## Prerequisites

- Docker 20.10+
- kubectl 1.28+
- kind 0.20+ (for local cluster)
- 8GB RAM minimum
- 50GB disk space

## Quick Start

### 1. Build Docker Images

```bash
./scripts/build.sh
```

This builds all service images:
- log-ingester:1.0.0
- query-api:1.0.0
- aggregator:1.0.0
- frontend:1.0.0

### 2. Setup Kubernetes Cluster

```bash
./scripts/setup-cluster.sh
```

Creates a kind cluster and loads all images.

### 3. Deploy the System

```bash
./scripts/deploy.sh
```

Deploys all components in the correct order:
1. Namespace and storage classes
2. Secrets
3. StatefulSets (TimescaleDB, Kafka, MinIO)
4. Deployments (services)
5. Monitoring stack

### 4. Verify Deployment

```bash
kubectl get pods -n log-analytics
```

Wait for all pods to be Running. StatefulSets take 2-3 minutes to fully initialize.

### 5. Access Services

```bash
# Frontend Dashboard
kubectl port-forward -n log-analytics svc/frontend 8080:80

# Grafana Monitoring
kubectl port-forward -n log-analytics svc/grafana 3000:3000
# Login: admin/admin

# Prometheus Metrics
kubectl port-forward -n log-analytics svc/prometheus 9090:9090
```

Visit:
- Frontend: http://localhost:8080
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### 6. Generate Test Data

```bash
./scripts/load-test.sh
```

Generates 1,000 log entries to test the system.

## Testing Persistent Storage

### Verify Data Persistence Across Pod Restarts

1. Generate logs:
```bash
./scripts/load-test.sh
```

2. Delete a TimescaleDB pod:
```bash
kubectl delete pod timescaledb-0 -n log-analytics
```

3. Wait for pod to restart:
```bash
kubectl wait --for=condition=ready pod timescaledb-0 -n log-analytics --timeout=300s
```

4. Query logs - data should still be present:
```bash
kubectl port-forward -n log-analytics svc/frontend 8080:80
```

Visit http://localhost:8080 and verify logs are displayed.

### Test Volume Expansion

1. Check current PVC size:
```bash
kubectl get pvc -n log-analytics
```

2. Edit PVC to request more storage:
```bash
kubectl edit pvc data-timescaledb-0 -n log-analytics
# Change storage: 10Gi to storage: 20Gi
```

3. Verify expansion:
```bash
kubectl get pvc data-timescaledb-0 -n log-analytics -o jsonpath='{.status.capacity.storage}'
```

### Test Data Recovery from Volume Snapshots

1. Create a volume snapshot:
\`\`\`bash
kubectl apply -f - <<YAML
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: timescaledb-snapshot
  namespace: log-analytics
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: data-timescaledb-0
YAML
\`\`\`

2. Restore from snapshot to a new PVC (disaster recovery simulation)

## Architecture Details

### TimescaleDB StatefulSet

- **Replicas**: 2 (primary + standby)
- **Storage**: 10Gi per replica with local-storage class
- **Resources**: 1 CPU / 2Gi memory (request), 2 CPU / 4Gi (limit)
- **Anti-affinity**: Ensures replicas run on different nodes
- **Probes**: Liveness and readiness checks for database health

Configuration optimized for time-series workloads:
- shared_buffers: 2GB
- effective_cache_size: 6GB
- Sequential write optimization for log ingestion

### Kafka StatefulSet

- **Replicas**: 1 (can scale to 3 for production)
- **Storage**: 5Gi persistent volume for commit logs
- **Retention**: 7 days (168 hours)
- **Resources**: 500m CPU / 1Gi memory

Persistent commit logs ensure:
- Zero message loss on pod restarts
- Consumer offset persistence
- Exactly-once delivery semantics

### MinIO StatefulSet

- **Replicas**: 1 (distributed mode requires 4+ nodes)
- **Storage**: 10Gi for log archival
- **Erasure Coding**: EC:2 (with 4 nodes, can lose 2 nodes)
- **S3 Compatibility**: Full S3 API for log archival

### Stateless Microservices

**Log Ingester**:
- HPA: 3-10 replicas based on CPU (70%) and memory (80%)
- Publishes to Kafka with acks=all for durability
- Prometheus metrics: logs_ingested_total, ingestion_duration_seconds

**Query API**:
- 2 replicas (stateless, can scale horizontally)
- Connection pool: 5-20 connections to TimescaleDB
- Supports time-range queries, filtering, and aggregations

**Aggregator**:
- 2 replicas consuming from Kafka
- Batch processing: 100 messages per transaction
- Exactly-once semantics with transaction commits

## Monitoring

### Prometheus Metrics

Key metrics collected:
- `logs_ingested_total`: Counter of ingested logs by level and source
- `log_ingestion_duration_seconds`: Histogram of ingestion latency
- `queries_executed_total`: Counter of executed queries
- `query_duration_seconds`: Histogram of query latency
- `kubelet_volume_stats_used_bytes`: Volume usage
- `kubelet_volume_stats_capacity_bytes`: Volume capacity

### Grafana Dashboards

Pre-configured dashboards for:
- Kubernetes cluster metrics
- Application metrics (ingestion rate, query performance)
- Storage metrics (PVC usage, I/O)
- Kafka metrics (message rate, consumer lag)

### Alerts

Production alerts configured for:
- PVC usage > 80%
- Pod CPU throttling > 50%
- Database connection pool exhaustion
- Kafka consumer lag > 10,000 messages
- Service error rate > 1%

## Troubleshooting

### Pods Stuck in Pending

**Symptom**: StatefulSet pods don't start

**Diagnosis**:
```bash
kubectl describe pod timescaledb-0 -n log-analytics
```

**Common causes**:
1. No PVs available to bind PVCs
2. Volume affinity mismatch (volume in zone A, pod scheduled to zone B)
3. Insufficient cluster resources

**Fix**:
```bash
# Check PVs
kubectl get pv

# Check PVCs
kubectl get pvc -n log-analytics

# Verify StorageClass
kubectl get storageclass
```

### Kafka Connection Errors

**Symptom**: Log ingester can't connect to Kafka

**Diagnosis**:
```bash
kubectl logs -n log-analytics deployment/log-ingester
```

**Fix**: Verify Kafka is ready
```bash
kubectl wait --for=condition=ready pod kafka-0 -n log-analytics --timeout=300s
```

### Data Loss After Pod Restart

**Symptom**: Logs disappear after pod restart

**Diagnosis**: Check if volumes are ephemeral
```bash
kubectl get pvc -n log-analytics
kubectl describe pv <pv-name>
```

**Root cause**: PVC using wrong StorageClass or volume with Delete reclaim policy

**Fix**: Ensure PVCs use StorageClass with Retain reclaim policy

### Volume Expansion Not Working

**Symptom**: PVC size doesn't increase after edit

**Diagnosis**:
```bash
kubectl describe pvc data-timescaledb-0 -n log-analytics
```

**Common causes**:
1. StorageClass doesn't have `allowVolumeExpansion: true`
2. CSI driver doesn't support expansion
3. Pod must be restarted for filesystem expansion

**Fix**:
```bash
# Verify StorageClass supports expansion
kubectl get storageclass local-storage -o yaml | grep allowVolumeExpansion

# Restart pod to trigger filesystem expansion
kubectl delete pod timescaledb-0 -n log-analytics
```

## Production Considerations

### Multi-Region Deployment

For production, deploy across multiple availability zones:

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: timescaledb
```

### Backup Strategy

1. **Volume Snapshots**: Automated daily snapshots via CronJob
2. **Database Dumps**: Logical backups with pg_dump
3. **Object Storage Replication**: MinIO to S3 for disaster recovery

### Capacity Planning

Monitor these metrics for scaling decisions:
- PVC usage: Alert at 70%, scale at 80%
- Database connection pool: Scale replicas if >80% utilization
- Kafka consumer lag: Add aggregator replicas if lag >5,000 messages
- Query latency: P99 <100ms target, scale query-api if breached

### Security Hardening

1. **Network Policies**: Restrict pod-to-pod communication
2. **RBAC**: Least-privilege service accounts
3. **Secrets Management**: Use external secret store (Vault, AWS Secrets Manager)
4. **Pod Security Standards**: Enforce restricted policy
5. **mTLS**: Enable Istio service mesh for encrypted communication

## Performance Tuning

### TimescaleDB Optimization

For write-heavy workloads:
- Increase `checkpoint_completion_target` to 0.9
- Tune `work_mem` based on query complexity
- Enable compression for old data partitions

### Kafka Optimization

For high throughput:
- Increase `num.io.threads` to 8
- Tune `log.segment.bytes` for optimal compaction
- Enable compression (snappy or lz4)

### Storage Class Selection

- **Fast SSD (gp3)**: Databases, message queues (3000 IOPS, 125 MB/s)
- **Standard HDD (gp2)**: Object storage, archival (baseline IOPS)
- **Local NVMe**: Maximum performance, requires data replication

## Cleanup

```bash
./scripts/cleanup.sh
```

This removes:
- All Kubernetes resources in log-analytics namespace
- Persistent Volumes
- Optionally, the kind cluster

## License

MIT

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.
