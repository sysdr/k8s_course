#!/usr/bin/env python3
"""
Comprehensive Observability Stack Diagnostic Tool
Checks entire metrics pipeline: ServiceMonitor -> Prometheus -> Grafana
"""
import sys
import json
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from datetime import datetime

@dataclass
class DiagnosticResult:
    component: str
    status: str  # "PASS", "FAIL", "WARN"
    message: str
    remediation: Optional[str] = None
    details: Optional[Dict] = None

class ObservabilityDiagnostics:
    def __init__(self):
        self.results: List[DiagnosticResult] = []
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
    
    def run_kubectl(self, args: List[str]) -> Dict:
        """Execute kubectl command and return JSON output"""
        try:
            cmd = ["kubectl"] + args + ["-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            return {"error": e.stderr}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON output"}
    
    def check_servicemonitor_labels(self):
        """Verify ServiceMonitor has required labels for Prometheus discovery"""
        print("🔍 Checking ServiceMonitor labels...")
        
        sm_data = self.run_kubectl([
            "get", "servicemonitor", "-n", "default", 
            "log-processor-broken", "-o", "json"
        ])
        
        if "error" in sm_data:
            self.results.append(DiagnosticResult(
                component="ServiceMonitor",
                status="FAIL",
                message="ServiceMonitor not found",
                remediation="Apply ServiceMonitor manifest: kubectl apply -f k8s/overlays/broken/"
            ))
            return
        
        labels = sm_data.get("metadata", {}).get("labels", {})
        required_label = "team"
        
        if required_label not in labels or labels[required_label] != "platform":
            self.results.append(DiagnosticResult(
                component="ServiceMonitor",
                status="FAIL",
                message=f"Missing required label: {required_label}=platform",
                remediation=(
                    "Add label to ServiceMonitor:\n"
                    "kubectl label servicemonitor log-processor-broken team=platform -n default\n"
                    "Or apply fixed version: kubectl apply -f k8s/overlays/fixed/"
                ),
                details={"current_labels": labels}
            ))
        else:
            self.results.append(DiagnosticResult(
                component="ServiceMonitor",
                status="PASS",
                message="ServiceMonitor has required labels"
            ))
    
    def check_service_selector_match(self):
        """Verify ServiceMonitor selector matches Service labels"""
        print("🔍 Checking ServiceMonitor <-> Service label matching...")
        
        # Get ServiceMonitor
        sm_data = self.run_kubectl([
            "get", "servicemonitor", "-n", "default", "-l", "app=log-processor"
        ])
        
        if not sm_data.get("items"):
            self.results.append(DiagnosticResult(
                component="Service Discovery",
                status="FAIL",
                message="No ServiceMonitor found for log-processor"
            ))
            return
        
        sm = sm_data["items"][0]
        sm_selector = sm["spec"]["selector"]["matchLabels"]
        
        # Get Service
        svc_data = self.run_kubectl([
            "get", "service", "log-processor", "-n", "default"
        ])
        
        if "error" in svc_data:
            self.results.append(DiagnosticResult(
                component="Service Discovery",
                status="FAIL",
                message="Service log-processor not found"
            ))
            return
        
        svc_labels = svc_data["metadata"]["labels"]
        
        # Check if all ServiceMonitor selector labels match Service labels
        mismatches = []
        for key, value in sm_selector.items():
            if key not in svc_labels or svc_labels[key] != value:
                mismatches.append(f"{key}={value}")
        
        if mismatches:
            self.results.append(DiagnosticResult(
                component="Service Discovery",
                status="FAIL",
                message=f"ServiceMonitor selector doesn't match Service labels",
                remediation=(
                    "Update ServiceMonitor selector to match Service labels:\n"
                    f"Service labels: {svc_labels}\n"
                    f"ServiceMonitor selector: {sm_selector}"
                ),
                details={
                    "service_labels": svc_labels,
                    "servicemonitor_selector": sm_selector,
                    "mismatches": mismatches
                }
            ))
        else:
            self.results.append(DiagnosticResult(
                component="Service Discovery",
                status="PASS",
                message="ServiceMonitor selector matches Service labels"
            ))
    
    def check_service_port_mapping(self):
        """Verify Service ports match ServiceMonitor endpoint ports"""
        print("🔍 Checking Service <-> ServiceMonitor port mappings...")
        
        # Get Service ports
        svc_data = self.run_kubectl([
            "get", "service", "log-processor", "-n", "default"
        ])
        
        svc_ports = {p["name"]: p["port"] for p in svc_data["spec"]["ports"]}
        
        # Get ServiceMonitor endpoints
        sm_data = self.run_kubectl([
            "get", "servicemonitor", "-n", "default", "-l", "app=log-processor"
        ])
        
        if sm_data.get("items"):
            sm = sm_data["items"][0]
            endpoints = sm["spec"]["endpoints"]
            
            for endpoint in endpoints:
                port_name = endpoint.get("port")
                
                if port_name not in svc_ports:
                    self.results.append(DiagnosticResult(
                        component="Port Mapping",
                        status="FAIL",
                        message=f"ServiceMonitor references non-existent port: {port_name}",
                        remediation=(
                            f"Update ServiceMonitor endpoint port to one of: {list(svc_ports.keys())}\n"
                            "For metrics, use port name 'metrics' instead of 'http'"
                        ),
                        details={
                            "available_ports": svc_ports,
                            "referenced_port": port_name
                        }
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        component="Port Mapping",
                        status="PASS",
                        message=f"Port {port_name} exists on Service"
                    ))
    
    def check_prometheus_targets(self):
        """Check Prometheus targets API to see if scraping is working"""
        print("🔍 Checking Prometheus scrape targets...")
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            data = response.json()
            
            if data["status"] != "success":
                self.results.append(DiagnosticResult(
                    component="Prometheus Targets",
                    status="FAIL",
                    message="Failed to query Prometheus targets API"
                ))
                return
            
            active_targets = data["data"]["activeTargets"]
            log_processor_targets = [
                t for t in active_targets 
                if "log-processor" in t.get("labels", {}).get("job", "")
            ]
            
            if not log_processor_targets:
                self.results.append(DiagnosticResult(
                    component="Prometheus Targets",
                    status="FAIL",
                    message="No active targets for log-processor",
                    remediation=(
                        "Check:\n"
                        "1. ServiceMonitor has team=platform label\n"
                        "2. ServiceMonitor selector matches Service labels\n"
                        "3. Prometheus serviceMonitorSelector configuration\n"
                        "\nDebug commands:\n"
                        "kubectl get servicemonitor -n default -o yaml\n"
                        "kubectl get service log-processor -n default -o yaml"
                    )
                ))
            else:
                healthy_targets = [t for t in log_processor_targets if t["health"] == "up"]
                
                if len(healthy_targets) == 0:
                    unhealthy = log_processor_targets[0]
                    self.results.append(DiagnosticResult(
                        component="Prometheus Targets",
                        status="FAIL",
                        message="Targets exist but are unhealthy",
                        remediation=f"Last error: {unhealthy.get('lastError', 'Unknown')}",
                        details={"target": unhealthy}
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        component="Prometheus Targets",
                        status="PASS",
                        message=f"{len(healthy_targets)} healthy targets scraping"
                    ))
        
        except requests.RequestException as e:
            self.results.append(DiagnosticResult(
                component="Prometheus Targets",
                status="FAIL",
                message=f"Cannot connect to Prometheus: {str(e)}",
                remediation="Port-forward Prometheus: kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090"
            ))
    
    def check_metrics_availability(self):
        """Query Prometheus for expected metrics"""
        print("🔍 Checking metrics availability in Prometheus...")
        
        expected_metrics = [
            "http_request_duration_seconds",
            "log_entries_processed_total",
            "active_processing_jobs"
        ]
        
        try:
            for metric in expected_metrics:
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": metric},
                    timeout=5
                )
                data = response.json()
                
                if data["status"] != "success":
                    self.results.append(DiagnosticResult(
                        component="Metrics Query",
                        status="FAIL",
                        message=f"Failed to query metric: {metric}"
                    ))
                    continue
                
                result_count = len(data["data"]["result"])
                
                if result_count == 0:
                    self.results.append(DiagnosticResult(
                        component="Metrics Query",
                        status="FAIL",
                        message=f"Metric {metric} has no data",
                        remediation=(
                            "Possible causes:\n"
                            "1. Application not exposing metrics correctly\n"
                            "2. Prometheus not scraping (check targets)\n"
                            "3. Metric name mismatch in queries\n"
                            "\nDebug:\n"
                            "curl http://log-processor:8080/metrics | grep http_request"
                        )
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        component="Metrics Query",
                        status="PASS",
                        message=f"Metric {metric} available ({result_count} series)"
                    ))
        
        except requests.RequestException as e:
            self.results.append(DiagnosticResult(
                component="Metrics Query",
                status="FAIL",
                message=f"Cannot query Prometheus: {str(e)}"
            ))
    
    def check_grafana_datasource(self):
        """Verify Grafana can connect to Prometheus"""
        print("🔍 Checking Grafana datasource health...")
        
        try:
            # Note: In production, use proper authentication
            response = requests.get(
                f"{self.grafana_url}/api/datasources",
                auth=("admin", "admin"),
                timeout=5
            )
            
            if response.status_code != 200:
                self.results.append(DiagnosticResult(
                    component="Grafana Datasource",
                    status="FAIL",
                    message="Cannot access Grafana API"
                ))
                return
            
            datasources = response.json()
            prometheus_ds = next(
                (ds for ds in datasources if ds["type"] == "prometheus"),
                None
            )
            
            if not prometheus_ds:
                self.results.append(DiagnosticResult(
                    component="Grafana Datasource",
                    status="FAIL",
                    message="No Prometheus datasource configured in Grafana",
                    remediation="Configure Prometheus datasource in Grafana UI"
                ))
            else:
                # Test datasource health
                ds_id = prometheus_ds["id"]
                health_response = requests.get(
                    f"{self.grafana_url}/api/datasources/{ds_id}/health",
                    auth=("admin", "admin"),
                    timeout=5
                )
                
                if health_response.status_code == 200:
                    self.results.append(DiagnosticResult(
                        component="Grafana Datasource",
                        status="PASS",
                        message="Grafana successfully connected to Prometheus"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        component="Grafana Datasource",
                        status="FAIL",
                        message="Grafana datasource health check failed",
                        details={"response": health_response.text}
                    ))
        
        except requests.RequestException as e:
            self.results.append(DiagnosticResult(
                component="Grafana Datasource",
                status="FAIL",
                message=f"Cannot connect to Grafana: {str(e)}",
                remediation="Port-forward Grafana: kubectl port-forward -n monitoring svc/grafana 3000:80"
            ))
    
    def run_all_checks(self):
        """Execute all diagnostic checks"""
        print("\n" + "="*70)
        print("  OBSERVABILITY STACK DIAGNOSTICS")
        print("="*70 + "\n")
        
        self.check_servicemonitor_labels()
        self.check_service_selector_match()
        self.check_service_port_mapping()
        self.check_prometheus_targets()
        self.check_metrics_availability()
        self.check_grafana_datasource()
        
        return self.results
    
    def print_results(self):
        """Print diagnostic results with color coding"""
        print("\n" + "="*70)
        print("  DIAGNOSTIC RESULTS")
        print("="*70 + "\n")
        
        status_colors = {
            "PASS": "\033[92m",  # Green
            "FAIL": "\033[91m",  # Red
            "WARN": "\033[93m",  # Yellow
        }
        reset_color = "\033[0m"
        
        pass_count = sum(1 for r in self.results if r.status == "PASS")
        fail_count = sum(1 for r in self.results if r.status == "FAIL")
        warn_count = sum(1 for r in self.results if r.status == "WARN")
        
        for result in self.results:
            color = status_colors.get(result.status, "")
            print(f"{color}[{result.status}]{reset_color} {result.component}: {result.message}")
            
            if result.remediation:
                print(f"  → Remediation: {result.remediation}")
            
            if result.details:
                print(f"  → Details: {json.dumps(result.details, indent=2)}")
            print()
        
        print("="*70)
        print(f"Summary: {pass_count} PASS, {fail_count} FAIL, {warn_count} WARN")
        print("="*70 + "\n")
        
        return fail_count == 0

if __name__ == "__main__":
    diagnostics = ObservabilityDiagnostics()
    diagnostics.run_all_checks()
    success = diagnostics.print_results()
    
    sys.exit(0 if success else 1)
