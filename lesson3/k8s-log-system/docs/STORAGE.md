# Persistent Storage Deep Dive

## Storage Architecture Layers

### 1. PersistentVolume (PV)
- **What**: Actual storage resource in the cluster
- **Created By**: Admin or dynamic provisioner
- **Lifecycle**: Independent of pods
- **Example**: 100GB SSD volume in AWS EBS

### 2. PersistentVolumeClaim (PVC)
- **What**: Request for storage by a pod
- **Created By**: Developers
- **Binding**: Matches to available PV or triggers dynamic provisioning
- **Example**: "I need 10GB with ReadWriteOnce access"

### 3. StorageClass
- **What**: Template for dynamic provisioning
- **Parameters**: Performance tier, replication, encryption
- **Provisioner**: Cloud-specific (AWS EBS, GCP PD, Azure Disk)
- **Example**: "fast-ssd" class provisions high-IOPS volumes

## StatefulSet Volume Management

```yaml
# Each pod gets its own PVC automatically
volumeClaimTemplates:
  - metadata:
      name: buffer-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi

# Results in:
# log-processor-0 → buffer-storage-log-processor-0 (10Gi)
# log-processor-1 → buffer-storage-log-processor-1 (10Gi)
# log-processor-2 → buffer-storage-log-processor-2 (10Gi)
```

## Access Modes

### ReadWriteOnce (RWO)
- **Meaning**: Single node can mount read-write
- **Use Case**: Databases, stateful apps
- **Cloud Examples**: AWS EBS, GCP PD
- **Limitation**: Pod must be on same node to access

### ReadOnlyMany (ROX)
- **Meaning**: Multiple nodes can mount read-only
- **Use Case**: Shared configuration, static assets
- **Example**: Container image layers

### ReadWriteMany (RWX)
- **Meaning**: Multiple nodes can mount read-write
- **Use Case**: Shared file systems
- **Cloud Examples**: AWS EFS, GCP Filestore
- **Cost**: 3-5x more expensive than RWO

## Storage Performance Tiers

### Hot Tier (SSD)
- **IOPS**: 3000-16000+
- **Use Case**: Active databases, real-time processing
- **Cost**: $$
- **Example**: TimescaleDB primary storage

### Warm Tier (Balanced)
- **IOPS**: 500-3000
- **Use Case**: Application logs, less active data
- **Cost**: $
- **Example**: Application buffer storage

### Cold Tier (HDD/Object Storage)
- **IOPS**: <500
- **Use Case**: Archives, backups
- **Cost**: $
- **Example**: S3/GCS for old logs

## Volume Binding Modes

### Immediate
- PVC immediately binds to PV
- **Risk**: Pod may schedule to node without access to volume
- **Use Case**: Pre-provisioned volumes

### WaitForFirstConsumer (Recommended)
- PVC binding waits for pod scheduling
- **Benefit**: Ensures pod and volume are on same node/zone
- **Use Case**: Dynamic provisioning

## Backup Strategies

### 1. Volume Snapshots
```bash
kubectl create volumesnapshot timescaledb-snapshot \
  --volume-snapshot-class=csi-snapshot-class \
  --source=timescaledb-pvc
```

### 2. Application-Level Backups
```bash
# PostgreSQL backup to S3
kubectl exec timescaledb-0 -- pg_dump -U postgres logs | \
  aws s3 cp - s3://backups/logs-$(date +%Y%m%d).sql
```

### 3. Disaster Recovery
- **RTO**: Recovery Time Objective
- **RPO**: Recovery Point Objective
- **Strategy**: Regular snapshots + transaction logs

## Monitoring Storage

```promql
# Volume usage
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100

# IOPS utilization
rate(node_disk_reads_completed_total[5m])
rate(node_disk_writes_completed_total[5m])

# Latency
rate(node_disk_read_time_seconds_total[5m])
rate(node_disk_write_time_seconds_total[5m])
```

## Common Issues

### PVC Pending
- **Cause**: No PV available or StorageClass missing
- **Fix**: Check StorageClass exists, verify provisioner

### Pod Stuck on Terminating
- **Cause**: Volume detachment timeout
- **Fix**: Force delete pod, check node health

### Out of Disk Space
- **Cause**: No monitoring, no cleanup
- **Fix**: Implement retention policies, alerts at 80%

### Volume Performance Degradation
- **Cause**: IOPS/throughput limits
- **Fix**: Upgrade to higher performance tier
