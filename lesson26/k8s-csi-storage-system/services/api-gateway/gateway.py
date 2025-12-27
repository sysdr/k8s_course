#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
INGESTION_URL = os.getenv('INGESTION_URL', 'http://log-ingestion:8080')
METRICS_FILE = os.getenv('METRICS_FILE', '/data/metrics/metrics.json')

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "API Gateway",
        "version": "1.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/metrics": "GET - Retrieve metrics",
            "/ingest": "POST - Ingest logs"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                data = json.load(f)
                return jsonify(data), 200
        return jsonify({"error": "metrics not available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ingest', methods=['POST'])
def ingest():
    try:
        response = requests.post(f"{INGESTION_URL}/ingest", json=request.get_json(), timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
