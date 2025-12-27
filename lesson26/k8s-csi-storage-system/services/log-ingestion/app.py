#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
import os
import time
from datetime import datetime

app = Flask(__name__)
LOG_FILE = os.getenv('LOG_FILE', '/data/logs/app.log')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ingest', methods=['POST'])
def ingest():
    try:
        data = request.get_json()
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": data.get("level", "INFO"),
            "message": data.get("message", ""),
            "source": data.get("source", "unknown")
        }
        
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return jsonify({"status": "success", "entry": log_entry}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
