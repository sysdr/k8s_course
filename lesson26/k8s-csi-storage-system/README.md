# Kubernetes CSI Storage System - Log Analytics

This project demonstrates a Kubernetes-based log analytics system using CSI storage.

## Architecture

- **Log Ingestion Service**: Receives and stores log entries
- **Log Processor Service**: Processes logs and generates metrics
- **API Gateway**: Exposes REST API for metrics and log ingestion
- **Frontend Dashboard**: Web UI for visualizing metrics

## Quick Start

1. Apply storage classes:
   ```bash
   kubectl apply -f k8s/storage/classes/
   ```

2. Start the system:
   ```bash
   ./scripts/start.sh
   ```

3. Run demo:
   ```bash
   ./scripts/demo.sh
   ```

4. Access dashboard:
   - Frontend: http://localhost:30000
   - API Gateway: http://localhost:30080

## Testing

Run tests:
```bash
./tests/test_system.sh
```

## Stopping

```bash
./scripts/stop.sh
```
