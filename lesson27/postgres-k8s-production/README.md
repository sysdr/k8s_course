# Production PostgreSQL on Kubernetes

A production-grade PostgreSQL deployment demonstrating stateful workloads in Kubernetes with high availability, automated failover, connection pooling, and comprehensive observability.

## System Architecture

### Components

**Database Layer:**
- PostgreSQL 16 StatefulSet with 3 replicas
- Streaming replication for high availability
- Persistent storage with fast SSD volumes
- Automated backup to external storage

**Connection Pooling:**
- PgBouncer for connection management
- Transaction-level pooling for optimal resource utilization
- Separate read-write and read-only endpoints

**Application Layer:**
- FastAPI microservice for database operations
- React dashboard for monitoring and analytics
- Horizontal Pod Autoscaling based on CPU/memory

**Service Mesh:**
- Istio for traffic management and security
- mTLS between services
- Circuit breaking and retry policies

**Observability:**
- Prometheus for metrics collection
- Grafana dashboards for visualization
- Custom metrics for database performance

## Quick Start

### Prerequisites

- Docker installed
- kubectl installed
- At least 8GB RAM available
- 20GB free disk space

### 1. Setup Local Cluster

```bash
./scripts/setup-cluster.sh
```

This creates a 3-node kind cluster with Istio and Prometheus Operator.

### 2. Build Images

```bash
./scripts/build.sh
```

Builds application images and loads them into the cluster.

### 3. Deploy System

```bash
./scripts/deploy.sh
```

Deploys PostgreSQL, PgBouncer, microservices, and monitoring stack.

### 4. Run Tests

```bash
./scripts/test.sh
```

Validates the deployment with integration tests.

### 5. Access Dashboard

```bash
kubectl port-forward -n services svc/frontend 8080:80
```

Open http://localhost:8080 in your browser.

## Architecture Details

### StatefulSet Configuration

The PostgreSQL StatefulSet provides:

1. **Stable Network Identity**: Each pod gets a predictable DNS name
   - postgres-0.postgres-headless.database.svc.cluster.local
   - postgres-1.postgres-headless.database.svc.cluster.local
   - postgres-2.postgres-headless.database.svc.cluster.local

2. **Persistent Storage**: Individual PVCs per pod
   - 50Gi fast-ssd volumes
   - Data survives pod rescheduling
   - Independent scaling and recovery

3. **Ordered Deployment**: Sequential pod creation
   - Primary initializes first
   - Replicas connect to primary for replication
   - Prevents split-brain scenarios

### High Availability

**Streaming Replication:**
- Asynchronous replication by default
- Replication lag monitoring via Prometheus
- Read replicas for query distribution

**Failover Strategy:**
- Manual failover (promotes replica to primary)
- Update service selector to point to new primary
- Applications reconnect automatically via service discovery

**Connection Pooling:**
- PgBouncer reduces connection overhead
- 1000 client connections → 25 backend connections
- Transaction-level pooling for OLTP workloads

### Resource Configuration

**PostgreSQL Pods:**
```yaml
resources:
  requests:
    memory: 2Gi    # Minimum for shared_buffers + connections
    cpu: 1000m     # 1 core baseline
  limits:
    memory: 4Gi    # OOM protection
    cpu: 2000m     # No throttling on checkpoints
```

**PgBouncer Pods:**
```yaml
resources:
  requests:
    memory: 64Mi   # Lightweight connection manager
    cpu: 100m
  limits:
    memory: 256Mi
    cpu: 500m
```

### Storage Configuration

**StorageClass: fast-ssd**
- Provisions SSD-backed volumes
- Required for IOPS-heavy workloads
- Cost: ~3x standard storage
- Performance: 50x IOPS improvement

**Persistent Volume Claims:**
- Individual 50Gi PVC per pod
- ReadWriteOnce access mode
- Reclaim policy: Retain (manual cleanup)
- Expansion enabled for growth

## Operational Procedures

### Backup and Restore

**Create Backup:**
```bash
./backup/backup.sh
```

Creates compressed pg_dump in /tmp/pg-backups/

**Restore from Backup:**
```bash
BACKUP_FILE="postgres-backup-20240115-120000.dump.gz"
PRIMARY_POD=$(kubectl get pod -n database -l app=postgres,role=primary -o jsonpath='{.items[0].metadata.name}')

# Copy backup to pod
gunzip -c "/tmp/pg-backups/$BACKUP_FILE" | \
  kubectl exec -i -n database "$PRIMARY_POD" -- \
  pg_restore -U postgres -d appdb -c
```

**Continuous WAL Archiving:**
Configure in postgresql.conf for point-in-time recovery:
```
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://bucket/wal/%f'
```

### Scaling

**Horizontal Scaling (Add Replicas):**
```bash
kubectl scale statefulset postgres -n database --replicas=5
```

New pods automatically:
- Attach to new PVCs
- Configure streaming replication
- Join read-only service pool

**Vertical Scaling (Increase Resources):**
```bash
# Update StatefulSet resources
kubectl edit statefulset postgres -n database

# Restart pods (one at a time)
kubectl rollout restart statefulset postgres -n database
```

**Storage Expansion:**
```bash
# Edit PVC size
kubectl edit pvc postgres-data-postgres-0 -n database

# Wait for resize
kubectl get pvc -n database -w
```

### Monitoring

**Key Metrics:**

1. **Replication Lag** (should be <1 second):
   ```sql
   SELECT client_addr, state, 
          pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
   FROM pg_stat_replication;
   ```

2. **Cache Hit Ratio** (should be >95%):
   ```sql
   SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 
   FROM pg_statio_user_tables;
   ```

3. **Connection Pool Utilization** (should be <80%):
   ```
   pgbouncer_pools_cl_active / pgbouncer_pools_cl_waiting
   ```

**Grafana Dashboards:**
- PostgreSQL Overview: Database metrics and performance
- Kubernetes Resources: Pod CPU, memory, storage
- Istio Service Mesh: Request rates, latency, errors

### Troubleshooting

**Pod Won't Start:**
```bash
# Check events
kubectl describe pod postgres-0 -n database

# Check logs
kubectl logs postgres-0 -n database -c postgres

# Common issues:
# - PVC not binding (check storage class)
# - Init container failed (permissions)
# - Config errors (check configmap)
```

**Replication Broken:**
```bash
# Check replication status
kubectl exec postgres-0 -n database -- \
  psql -U postgres -c "SELECT * FROM pg_stat_replication;"

# If empty, replicas can't connect
# Check pg_hba.conf allows replication
# Verify network policies
```

**High Replication Lag:**
```bash
# Check WAL sender queue
kubectl exec postgres-0 -n database -- \
  psql -U postgres -c "SELECT * FROM pg_stat_wal_sender;"

# Possible causes:
# - Network latency between pods
# - Replica under heavy load
# - Insufficient replica resources
```

**Connection Pool Exhaustion:**
```bash
# Check PgBouncer stats
kubectl exec -n database deployment/pgbouncer -- \
  psql -p 5432 -U pgbouncer pgbouncer -c "SHOW POOLS;"

# Increase pool size if needed
kubectl edit configmap pgbouncer-config -n database
```

**Disk Space Issues:**
```bash
# Check PVC usage
kubectl exec postgres-0 -n database -- df -h /var/lib/postgresql/data

# If >80% full:
# 1. Expand PVC (see scaling section)
# 2. Clean old WAL segments
# 3. Vacuum database
kubectl exec postgres-0 -n database -- \
  psql -U postgres -d appdb -c "VACUUM FULL;"
```

## Performance Tuning

### PostgreSQL Configuration

**Memory Settings:**
```
shared_buffers = 25% of total memory
effective_cache_size = 75% of total memory
work_mem = Total memory / max_connections / 2
maintenance_work_mem = 256MB - 2GB
```

**Connection Settings:**
```
max_connections = 200 (with PgBouncer)
superuser_reserved_connections = 3
```

**WAL Settings:**
```
wal_level = replica
max_wal_size = 2GB
wal_compression = on
```

### Query Optimization

**Enable pg_stat_statements:**
```sql
CREATE EXTENSION pg_stat_statements;

-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Create Indexes:**
```sql
-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY abs(correlation) DESC;
```

## Security Best Practices

**Secrets Management:**
- Store credentials in Kubernetes Secrets
- Use External Secrets Operator for production
- Rotate passwords regularly

**Network Policies:**
- Restrict database access to application namespace
- Block external traffic to PostgreSQL ports
- Use Istio AuthorizationPolicies

**RBAC:**
- Least-privilege ServiceAccounts
- Separate roles for admin and application access
- Audit logs for privileged operations

**Encryption:**
- mTLS via Istio for service-to-service
- TLS for client connections
- Encryption at rest for PVCs (cloud provider)

## Cost Optimization

**Resource Right-Sizing:**
- Monitor actual usage vs requests
- Adjust CPU/memory based on metrics
- Use Vertical Pod Autoscaler

**Storage Optimization:**
- Compress old data
- Archive unused tables
- Regular vacuuming

**Replica Optimization:**
- Scale replicas based on read load
- Use pod anti-affinity for HA
- Consider read-only pools

## Production Considerations

**Before Going to Production:**

1. **Backup Strategy:**
   - Automated daily base backups
   - Continuous WAL archiving
   - Test restore procedures monthly
   - Document RPO/RTO requirements

2. **Disaster Recovery:**
   - Multi-region replication
   - Automated failover procedures
   - Runbook for manual intervention
   - Regular DR drills

3. **Monitoring:**
   - Alert on replication lag >5s
   - Alert on connection pool >80%
   - Alert on disk usage >80%
   - Alert on cache hit ratio <95%

4. **Security:**
   - Rotate database credentials
   - Enable audit logging
   - Network policies enforced
   - Regular security patches

5. **Capacity Planning:**
   - Monitor growth trends
   - Plan storage expansion
   - Test scaling procedures
   - Budget for infrastructure costs

## Cleanup

```bash
./scripts/cleanup.sh
```

Removes all resources including PVCs and namespaces.

To delete the entire cluster:
```bash
kind delete cluster --name postgres-ha
```

## Architecture Decisions

### Why StatefulSets?

Deployments are designed for stateless applications where:
- Pods are interchangeable
- Random pod names are acceptable
- Storage is ephemeral or shared

Databases require:
- Stable network identities for replication
- Individual persistent storage per instance
- Ordered, graceful scaling and termination

### Why PgBouncer?

PostgreSQL creates a backend process per connection:
- Memory overhead: ~10MB per connection
- Connection establishment: 50-200ms
- Max connections limit: 100-400 typical

PgBouncer provides:
- Connection pooling: 1000 clients → 25 backends
- Connection multiplexing
- Reduced memory footprint
- Faster connection establishment

### Why Istio?

Benefits:
- mTLS without application changes
- Traffic management (retries, timeouts)
- Observability (traces, metrics)
- Fine-grained access control

Trade-offs:
- Increased complexity
- Memory overhead per pod
- Learning curve

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Istio Service Mesh](https://istio.io/latest/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)

## Support

For issues or questions:
- GitHub Issues: [your-repo]/issues
- Slack: #database-ops
- Email: sre@example.com
