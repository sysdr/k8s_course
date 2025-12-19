# Secrets Management Architecture

## System Overview

The platform implements a five-layer security architecture for managing secrets in Kubernetes, mirroring patterns used by Datadog and Splunk.

## Layer 1: Kubernetes Native Secrets

- Base64-encoded key-value pairs stored in etcd
- Mounted as volumes or environment variables
- Limited to 1MB per secret
- Requires etcd encryption at rest for production

## Layer 2: External Secrets Integration

- Vault Simulator provides centralized secret store
- Automatic synchronization to Kubernetes secrets
- Token-based authentication
- Audit logging for all operations

## Layer 3: Volume Mounts with Hot-Reload

- Secrets mounted as read-only files (0400 permissions)
- File modification time monitoring for changes
- 30-second poll interval for updates
- No pod restart required

## Layer 4: mTLS Encryption

- Istio automatic mutual TLS
- Certificate rotation every 24 hours
- Traffic encrypted between all pods
- Zero-trust network model

## Layer 5: Audit and Compliance

- PostgreSQL-backed audit log
- All secret access operations logged
- Tamper-proof append-only design
- 90-day retention for compliance

## Secret Rotation Flow

```
┌─────────────┐
│   Vault     │  1. Generate new secret
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  External   │  2. Sync to K8s Secret
│  Secrets    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Volume     │  3. Update mounted file
│  Mount      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Service    │  4. Detect change & reload
│  Pod        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │  5. Use new credential
│  Connection │
└─────────────┘
```

## Failure Modes and Recovery

### Vault Unavailable
- Services use cached secrets (5-minute TTL)
- Alert triggers after 2 minutes
- Automatic recovery on Vault restore

### Secret Mount Failure
- Readiness probe fails
- Pod not added to service endpoints
- Traffic routes to healthy pods

### Database Connection Lost
- Connection pool retry with exponential backoff
- Circuit breaker prevents cascading failures
- Automatic reconnection on credential update

## Security Boundaries

- **Namespace Isolation**: Each tenant in separate namespace
- **RBAC**: Service accounts with minimal permissions
- **Network Policies**: Pod-to-pod communication restricted
- **Pod Security**: Non-root containers, read-only filesystems
