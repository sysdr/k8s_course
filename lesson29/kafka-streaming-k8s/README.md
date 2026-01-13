# Kafka Streaming Pipeline on Kubernetes

A production-ready Kafka streaming pipeline deployed on Kubernetes with monitoring, logging, and a real-time dashboard.

## Architecture

- **ZooKeeper**: 3-node cluster for Kafka coordination
- **Kafka**: 3-node cluster for message streaming
- **Producer**: FastAPI service for producing log events
- **Consumer**: Python service for consuming and processing events
- **Redis**: In-memory data store for real-time statistics
- **API**: FastAPI service for querying statistics
- **Frontend**: React dashboard for visualization

## Quick Start

1. Run the setup script:
   ```bash
   ./scripts/startup.sh
   ```

2. Or run steps individually:
   ```bash
   ./scripts/setup-cluster.sh
   ./scripts/build.sh
   ./scripts/deploy.sh
   ```

3. Run demo to generate events:
   ```bash
   ./scripts/demo.sh
   ```

4. Access the dashboard:
   ```bash
   kubectl port-forward -n kafka-pipeline svc/frontend 8080:80
   ```
   Then open http://localhost:8080

## Testing

Run tests:
```bash
./scripts/test.sh
```

## Monitoring

Check pod status:
```bash
kubectl get pods -n kafka-pipeline
```

View logs:
```bash
kubectl logs -n kafka-pipeline -l app=producer
kubectl logs -n kafka-pipeline -l app=consumer
```
