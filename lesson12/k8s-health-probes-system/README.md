# Kubernetes Health Probes & Lifecycle System

A production-grade log analytics platform demonstrating health probe patterns and lifecycle management for self-healing Kubernetes applications.

## System Overview

This system implements three microservices with different health probe configurations:

- **Log Collector**: Fast startup with graceful buffer flushing
- **Log Processor**: Slow startup (ML model loading) with cache warming
- **Analytics API**: High-availability with connection draining

## Quick Start

```bash
# Build images
./scripts/build.sh

# Setup local cluster
./scripts/setup-cluster.sh

# Deploy system
./scripts/deploy.sh

# Test health probes
./scripts/test-health-probes.sh
```

## Health Probe Architecture

### Three-Probe Model

| Probe Type | Purpose | What It Checks |
|------------|---------|----------------|
| **Liveness** | Is the process broken? | Internal state only |
| **Readiness** | Can it handle traffic? | Dependencies, resources |
| **Startup** | Has it finished initializing? | Initialization complete |

### Key Configuration Parameters

```yaml
livenessProbe:
  initialDelaySeconds: 10    # Wait for basic startup
  periodSeconds: 10          # Check frequency
  timeoutSeconds: 5          # Response timeout
  failureThreshold: 3        # Failures before restart
```

### Anti-Patterns Avoided

1. **Liveness checking dependencies**: Never check database/cache in liveness
2. **Same endpoint for all probes**: Each probe type has dedicated endpoint
3. **No startup probe for slow apps**: Use startup probe instead of long initialDelay

## Service-Specific Configurations

### Log Collector
- **Startup**: Fast (60s max)
- **preStop**: Flush buffers before termination
- **Grace period**: 60s for buffer flushing

### Log Processor
- **Startup**: Slow (120s max for ML model)
- **postStart**: Trigger cache warming
- **Startup probe**: Prevents liveness killing during init

### Analytics API
- **preStop**: 10s sleep for connection draining
- **Strategy**: RollingUpdate with maxUnavailable: 0
- **Grace period**: 60s for request completion

## Testing Self-Healing

```bash
# Simulate pod failure
./scripts/simulate-failure.sh

# Watch pod restarts
kubectl get pods -n log-analytics -w

# Monitor events
kubectl get events -n log-analytics --sort-by='.lastTimestamp'
```

## Monitoring

Health probe metrics to watch:

- `kube_pod_container_status_restarts_total`: Restart frequency
- `kube_pod_status_ready`: Ready state changes
- Custom `/metrics` endpoints for application health

### Alerts

- **PodNotReady**: Pod not ready for >5 minutes
- **HighRestartCount**: >3 restarts per hour
- **SlowStartup**: Pod in ContainerCreating >3 minutes

## Directory Structure

```
├── src/
│   ├── log-collector/     # Fast-startup service
│   ├── log-processor/     # Slow-startup with ML
│   ├── analytics-api/     # HA user-facing API
│   └── frontend/          # React dashboard
├── k8s/
│   └── base/              # Kubernetes manifests
├── helm/                  # Helm chart
├── monitoring/            # Prometheus/Grafana
├── istio/                 # Service mesh config
└── scripts/               # Operational scripts
```

## Production Considerations

### Probe Tuning Guidelines

1. **timeoutSeconds**: Set above P99 latency
2. **failureThreshold**: 3+ to tolerate transient failures
3. **periodSeconds**: Balance freshness vs resource usage

### Graceful Shutdown Sequence

1. preStop hook executes
2. Pod marked not ready (removed from Service)
3. SIGTERM sent to container
4. Wait for terminationGracePeriodSeconds
5. SIGKILL if still running

### Resource Interaction

Probes consume resources. For 100 pods with 10s probe interval:
- 600 health checks per minute
- Consider TCP probes for simple port checks

## Troubleshooting

### Pod CrashLoopBackOff
Check if liveness probe is too aggressive:
```bash
kubectl describe pod <pod-name> -n log-analytics
kubectl logs <pod-name> -n log-analytics --previous
```

### Pods Not Receiving Traffic
Check readiness probe and endpoints:
```bash
kubectl get endpoints -n log-analytics
kubectl describe pod <pod-name> -n log-analytics | grep -A5 Readiness
```

### Slow Rollouts
Check startup probe configuration:
```bash
kubectl get events -n log-analytics | grep -i probe
```

## Cleanup

```bash
./scripts/cleanup.sh
```
