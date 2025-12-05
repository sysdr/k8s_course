#!/usr/bin/env python3
"""
Dashboard Server for Kubernetes Debugging Challenge
Provides a web interface to view project outcomes, system status, and monitoring operations.
"""

from flask import Flask, render_template, jsonify, request
import os
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Sample metrics data
def generate_sample_metrics() -> Dict:
    """Generate sample Prometheus metrics data"""
    now = datetime.now()
    timestamps = [(now - timedelta(minutes=i)).isoformat() for i in range(60, -1, -1)]
    
    # Generate realistic-looking HTTP request metrics
    base_requests = 100
    request_data = []
    for ts in timestamps:
        # Simulate varying request rates
        value = base_requests + random.randint(-20, 30)
        request_data.append({
            "timestamp": ts,
            "value": max(0, value)
        })
    
    # Generate latency metrics
    base_latency = 0.15
    latency_data = []
    for ts in timestamps:
        value = base_latency + random.uniform(-0.05, 0.08)
        latency_data.append({
            "timestamp": ts,
            "value": max(0.01, round(value, 3))
        })
    
    return {
        "http_requests_total": request_data,
        "http_request_duration_seconds": latency_data
    }

# Sample Prometheus queries
PROMETHEUS_QUERIES = {
    "http_requests_total": {
        "query": "sum(rate(http_requests_total[5m])) by (endpoint)",
        "description": "Request rate per endpoint over 5 minutes",
        "result_type": "vector"
    },
    "http_request_duration_seconds": {
        "query": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
        "description": "95th percentile latency by endpoint",
        "result_type": "vector"
    },
    "error_rate": {
        "query": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
        "description": "Error rate percentage",
        "result_type": "scalar"
    },
    "request_count_by_method": {
        "query": "sum(http_requests_total) by (method)",
        "description": "Total requests by HTTP method",
        "result_type": "vector"
    }
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/system-status')
def system_status():
    """Get system status information"""
    # In a real implementation, this would query kubectl or Kubernetes API
    # Returns sample data
    return jsonify({
        "namespace": "debugging-challenge",
        "pods": {
            "frontend": {
                "status": "Running",
                "ready": "2/2",
                "restarts": 0,
                "age": "5m"
            },
            "backend": {
                "status": "Running",
                "ready": "2/2",
                "restarts": 0,
                "age": "5m"
            },
            "database": {
                "status": "Running",
                "ready": "1/1",
                "restarts": 0,
                "age": "5m"
            }
        },
        "services": {
            "frontend-service": {"type": "ClusterIP", "ports": "80/TCP"},
            "backend-service": {"type": "ClusterIP", "ports": "8080/TCP"},
            "database-service": {"type": "ClusterIP", "ports": "5432/TCP"}
        },
        "ingress": {
            "ecommerce-ingress": {"hosts": "ecommerce.local", "address": "pending"}
        },
        "network_policies": 2,
        "istio_resources": {
            "virtualservices": 1,
            "destinationrules": 1
        }
    })

@app.route('/api/prometheus/query', methods=['POST'])
def prometheus_query():
    """Prometheus query endpoint"""
    data = request.get_json()
    query = data.get('query', '')
    
    # Simulate query execution
    time.sleep(0.5)  # Simulate query processing time
    
    # Return results based on query type
    if 'http_requests_total' in query:
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"endpoint": "/products", "method": "GET"},
                        "value": [int(time.time()), str(random.randint(150, 250))]
                    },
                    {
                        "metric": {"endpoint": "/health", "method": "GET"},
                        "value": [int(time.time()), str(random.randint(50, 100))]
                    },
                    {
                        "metric": {"endpoint": "/metrics", "method": "GET"},
                        "value": [int(time.time()), str(random.randint(10, 30))]
                    }
                ]
            }
        })
    elif 'http_request_duration_seconds' in query:
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"endpoint": "/products"},
                        "value": [int(time.time()), str(round(random.uniform(0.10, 0.25), 3))]
                    },
                    {
                        "metric": {"endpoint": "/health"},
                        "value": [int(time.time()), str(round(random.uniform(0.01, 0.05), 3))]
                    }
                ]
            }
        })
    elif 'error_rate' in query:
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "scalar",
                "result": [int(time.time()), str(round(random.uniform(0.0, 0.05), 4))]
            }
        })
    else:
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"method": "GET"},
                        "value": [int(time.time()), str(random.randint(500, 800))]
                    },
                    {
                        "metric": {"method": "POST"},
                        "value": [int(time.time()), str(random.randint(50, 150))]
                    }
                ]
            }
        })

@app.route('/api/prometheus/queries')
def list_prometheus_queries():
    """Get list of available Prometheus queries"""
    return jsonify(PROMETHEUS_QUERIES)

@app.route('/api/grafana/metrics')
def grafana_metrics():
    """Get metrics data for Grafana-like visualization"""
    metrics = generate_sample_metrics()
    return jsonify(metrics)

@app.route('/api/project-info')
def project_info():
    """Get project information"""
    return jsonify({
        "name": "Kubernetes Networking Debugging Challenge",
        "description": "E-Commerce system with 5 intentional networking bugs to debug",
        "architecture": {
            "layers": [
                {
                    "name": "Layer 1: Ingress",
                    "description": "External → Internal routing",
                    "component": "nginx-ingress"
                },
                {
                    "name": "Layer 2: Service Discovery",
                    "description": "Service → Pods mapping",
                    "component": "Kubernetes Services"
                },
                {
                    "name": "Layer 3: NetworkPolicy",
                    "description": "Pod → Pod communication rules",
                    "component": "NetworkPolicies"
                },
                {
                    "name": "Layer 4: Service Mesh",
                    "description": "Istio traffic routing",
                    "component": "VirtualService & DestinationRule"
                },
                {
                    "name": "Layer 5: DNS Resolution",
                    "description": "Service name resolution",
                    "component": "CoreDNS"
                }
            ]
        },
        "bugs": [
            "Ingress Routing: Service name misconfiguration",
            "Service Discovery: Label selector mismatch",
            "NetworkPolicy: Overly restrictive egress rules",
            "Istio VirtualService: Routing to non-existent subset",
            "Service Mesh: Missing DestinationRule subset definition"
        ],
        "components": [
            "Frontend (React/nginx)",
            "Backend (FastAPI/Python)",
            "Database (PostgreSQL)",
            "Monitoring (Prometheus & Grafana)",
            "Service Mesh (Istio)"
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

