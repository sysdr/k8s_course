#!/usr/bin/env python3
"""
Dashboard Server for Kubernetes Log Processing System
Serves the dashboard HTML and provides API endpoints for cluster data
"""
import json
import os
import subprocess
import http.server
import socketserver
import urllib.parse
import traceback
from pathlib import Path
from datetime import datetime

PORT = 8080

def run_kubectl_command(cmd):
    """Execute kubectl command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except subprocess.CalledProcessError:
        return ""

def get_nodes():
    """Get cluster nodes information"""
    output = run_kubectl_command("kubectl get nodes -o json")
    if not output:
        return []
    
    try:
        data = json.loads(output)
        nodes = []
        for item in data.get('items', []):
            status = "Ready"
            for condition in item.get('status', {}).get('conditions', []):
                if condition.get('type') == 'Ready':
                    status = "Ready" if condition.get('status') == 'True' else "NotReady"
                    break
            
            role = "worker"
            for label, value in item.get('metadata', {}).get('labels', {}).items():
                if 'node-role.kubernetes.io/control-plane' in label or 'node-role.kubernetes.io/master' in label:
                    role = "control-plane"
                    break
            
            nodes.append({
                'name': item.get('metadata', {}).get('name', 'unknown'),
                'status': status,
                'role': role,
                'version': item.get('status', {}).get('nodeInfo', {}).get('kubeletVersion', 'unknown'),
                'age': calculate_age(item.get('metadata', {}).get('creationTimestamp', ''))
            })
        return nodes
    except json.JSONDecodeError:
        return []

def get_pods():
    """Get all pods information"""
    output = run_kubectl_command("kubectl get pods -A -o json")
    if not output:
        return []
    
    try:
        data = json.loads(output)
        pods = []
        for item in data.get('items', []):
            status = item.get('status', {}).get('phase', 'Unknown')
            ready_containers = sum(1 for c in item.get('status', {}).get('containerStatuses', []) if c.get('ready', False))
            total_containers = len(item.get('status', {}).get('containerStatuses', []))
            restarts = sum(c.get('restartCount', 0) for c in item.get('status', {}).get('containerStatuses', []))
            
            pods.append({
                'name': item.get('metadata', {}).get('name', 'unknown'),
                'namespace': item.get('metadata', {}).get('namespace', 'default'),
                'status': status,
                'ready': f"{ready_containers}/{total_containers}",
                'restarts': restarts,
                'age': calculate_age(item.get('metadata', {}).get('creationTimestamp', ''))
            })
        return pods
    except json.JSONDecodeError:
        return []

def get_services():
    """Get services information"""
    output = run_kubectl_command("kubectl get services -A -o json")
    if not output:
        return []
    
    try:
        data = json.loads(output)
        services = []
        for item in data.get('items', []):
            services.append({
                'name': item.get('metadata', {}).get('name', 'unknown'),
                'namespace': item.get('metadata', {}).get('namespace', 'default'),
                'type': item.get('spec', {}).get('type', 'ClusterIP')
            })
        return services
    except json.JSONDecodeError:
        return []

def calculate_age(timestamp_str):
    """Calculate age from timestamp"""
    if not timestamp_str:
        return "unknown"
    try:
        # Parse ISO format timestamp
        created = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.utcnow()
        if created.tzinfo:
            now = datetime.now(created.tzinfo)
        delta = now - created.replace(tzinfo=None) if created.tzinfo else now - created
        
        if delta.days > 0:
            return f"{delta.days}d"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m"
        else:
            return f"{delta.seconds}s"
    except:
        return "unknown"

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            
            if parsed_path.path == '/api/cluster-data':
                # Return cluster data as JSON
                try:
                    data = {
                        'nodes': get_nodes(),
                        'pods': get_pods(),
                        'services': get_services(),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    response_data = json.dumps(data).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(response_data)
                    self.wfile.flush()
                    self.wfile.close()
                except Exception as e:
                    # Return error response
                    error_data = json.dumps({
                        'error': str(e),
                        'nodes': [],
                        'pods': [],
                        'services': [],
                        'timestamp': datetime.utcnow().isoformat()
                    }).encode()
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(error_data)))
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(error_data)
                    self.wfile.flush()
                    self.wfile.close()
            elif parsed_path.path == '/' or parsed_path.path == '/dashboard.html':
                # Serve dashboard HTML
                self.path = '/dashboard.html'
                return super().do_GET()
            else:
                # Serve other files
                return super().do_GET()
        except Exception as e:
            print(f"Error handling request: {e}")
            traceback.print_exc()
            try:
                self.send_error(500, f"Internal Server Error: {str(e)}")
            except:
                pass
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        # Only log errors
        try:
            if len(args) > 1 and args[1].startswith('5'):
                print(f"[{self.log_date_time_string()}] {format % args}")
        except:
            pass

def main():
    """Start the dashboard server"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    with ReusableTCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"🚀 Dashboard server starting...")
        print(f"📊 Dashboard available at: http://localhost:{PORT}")
        print(f"🌐 Open in browser: http://localhost:{PORT}/dashboard.html")
        print(f"\nPress Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down dashboard server...")
            httpd.shutdown()

if __name__ == "__main__":
    main()

