from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
from kubernetes import client, config
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Test Results Aggregator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kubernetes client (optional - only if running in K8s)
v1 = None
try:
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        logger.info("Kubernetes client initialized (in-cluster)")
    except:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        logger.info("Kubernetes client initialized (kube-config)")
except Exception as e:
    logger.warning(f"Kubernetes client not available (running outside K8s): {e}")
    v1 = None

class TestResult(BaseModel):
    job_name: str
    test_suite: str
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    timestamp: str
    details: Optional[Dict] = None

# In-memory test results
test_results = []

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/results", status_code=201)
async def submit_test_result(result: TestResult):
    """Submit test results from a test Job"""
    test_results.append(result)
    logger.info(f"Received results from {result.job_name}: {result.passed} passed, {result.failed} failed")
    
    # Store in ConfigMap for persistence (only if K8s client is available)
    if v1 is not None:
        try:
            configmap_name = f"test-result-{result.job_name.replace('_', '-')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=configmap_name,
                    labels={
                        "app": "test-results",
                        "test-suite": result.test_suite
                    }
                ),
                data={
                    "results.json": result.json()
                }
            )
            
            v1.create_namespaced_config_map(namespace="default", body=configmap)
            logger.info(f"Stored results in ConfigMap {configmap_name}")
            
        except Exception as e:
            logger.error(f"Failed to store results in ConfigMap: {e}")
    else:
        logger.info("Kubernetes not available - results stored in memory only")
    
    return {"status": "accepted", "result_id": len(test_results) - 1}

@app.get("/api/v1/results", response_model=List[TestResult])
async def get_test_results(test_suite: Optional[str] = None):
    """Get all test results or filter by suite"""
    results = test_results
    
    if test_suite:
        results = [r for r in results if r.test_suite == test_suite]
    
    return results

@app.get("/api/v1/results/summary")
async def get_test_summary():
    """Get summary of all test results"""
    if not test_results:
        return {
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "pass_rate": 0.0,
            "test_suites": 0
        }
    
    total_passed = sum(r.passed for r in test_results)
    total_failed = sum(r.failed for r in test_results)
    total_tests = total_passed + total_failed
    
    return {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0.0,
        "test_suites": len(set(r.test_suite for r in test_results)),
        "latest_run": test_results[-1].timestamp if test_results else None
    }

@app.get("/api/v1/gate/check")
async def check_quality_gate():
    """Check if tests pass quality gates for deployment"""
    if not test_results:
        return {
            "gate_passed": False,
            "reason": "No test results available"
        }
    
    # Get latest results for each test suite
    latest_results = {}
    for result in test_results:
        if result.test_suite not in latest_results or result.timestamp > latest_results[result.test_suite].timestamp:
            latest_results[result.test_suite] = result
    
    # Check quality gates
    total_passed = sum(r.passed for r in latest_results.values())
    total_failed = sum(r.failed for r in latest_results.values())
    total_tests = total_passed + total_failed
    
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0
    
    # Gate: 95% pass rate required
    gate_passed = pass_rate >= 95.0 and total_failed == 0
    
    return {
        "gate_passed": gate_passed,
        "pass_rate": pass_rate,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "threshold": 95.0,
        "suites_checked": list(latest_results.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
