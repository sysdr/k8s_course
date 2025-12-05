# Dashboard Server

A professional web dashboard for the Kubernetes Debugging Challenge project that provides:

- **Project Overview**: System architecture, bugs, and components
- **System Status**: Real-time pod, service, and ingress status
- **Prometheus**: Interactive query interface with sample queries
- **Grafana**: Time-series graphs and metrics visualization

## Features

- Modern, professional UI (teal/orange/green color scheme)
- Interactive Prometheus query interface
- Grafana-like graph visualizations
- Real-time system status updates
- Responsive design

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The dashboard will be available at `http://localhost:5000`

## Building Docker Image

```bash
docker build -t dashboard:latest .
```

## Accessing in Kubernetes

After deployment, use port-forward to access:

```bash
kubectl port-forward -n debugging-challenge svc/dashboard-service 5000:5000
```

Then open `http://localhost:5000` in your browser.

## API Endpoints

- `GET /` - Main dashboard page
- `GET /api/system-status` - Get system status information
- `GET /api/project-info` - Get project information
- `GET /api/prometheus/queries` - List available sample queries
- `POST /api/prometheus/query` - Execute a Prometheus query
- `GET /api/grafana/metrics` - Get metrics data for visualization

