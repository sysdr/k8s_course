import pytest
import httpx
import asyncio
import os
import json
from datetime import datetime

# Service URLs
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")
TEST_RESULTS_URL = os.getenv("TEST_RESULTS_URL", "http://test-results-aggregator:8003")

class TestOrderFlow:
    """Integration tests for complete order flow"""
    
    @pytest.mark.asyncio
    async def test_complete_order_flow(self):
        """Test end-to-end order creation, payment, and fulfillment"""
        async with httpx.AsyncClient() as client:
            # 1. Get available products
            response = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products")
            assert response.status_code == 200
            products = response.json()
            assert len(products) > 0
            
            # 2. Create order
            order_data = {
                "user_id": "test-user-001",
                "items": [
                    {"product_id": products[0]["id"], "quantity": 2}
                ]
            }
            
            response = await client.post(
                f"{ORDER_SERVICE_URL}/api/v1/orders",
                json=order_data,
                timeout=10.0
            )
            assert response.status_code == 201
            order = response.json()
            assert order["status"] == "confirmed"
            assert order["payment_id"] is not None
            
            # 3. Verify payment was processed
            payment_id = order["payment_id"]
            response = await client.get(f"{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_id}")
            assert response.status_code == 200
            payment = response.json()
            assert payment["status"] == "completed"
            assert payment["amount"] == order["total_amount"]
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_handling(self):
        """Test order fails gracefully when stock is insufficient"""
        async with httpx.AsyncClient() as client:
            # Try to order excessive quantity
            order_data = {
                "user_id": "test-user-002",
                "items": [
                    {"product_id": "prod-001", "quantity": 10000}
                ]
            }
            
            response = await client.post(
                f"{ORDER_SERVICE_URL}/api/v1/orders",
                json=order_data,
                timeout=10.0
            )
            # Should fail with 400 due to insufficient stock
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_service_health_checks(self):
        """Verify all services are healthy"""
        services = [
            (PRODUCT_SERVICE_URL, "product-service"),
            (ORDER_SERVICE_URL, "order-service"),
            (PAYMENT_SERVICE_URL, "payment-service")
        ]
        
        async with httpx.AsyncClient() as client:
            for service_url, service_name in services:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                assert response.status_code == 200, f"{service_name} health check failed"
                health_data = response.json()
                assert health_data["status"] == "healthy"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    # Run tests and collect results
    import subprocess
    import sys
    
    start_time = datetime.utcnow()
    
    # Run pytest with json report
    result = subprocess.run(
        ["pytest", __file__, "-v", "--json-report", "--json-report-file=/tmp/test-results.json"],
        capture_output=True,
        text=True
    )
    
    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Parse results
    try:
        with open("/tmp/test-results.json", "r") as f:
            test_data = json.load(f)
        
        passed = test_data["summary"]["passed"]
        failed = test_data["summary"]["failed"]
        
    except:
        # Fallback if json report fails
        passed = 0 if result.returncode != 0 else 3
        failed = 3 if result.returncode != 0 else 0
    
    # Submit results to aggregator
    asyncio.run(submit_results(passed, failed, duration_ms))
    
    sys.exit(result.returncode)

async def submit_results(passed, failed, duration_ms):
    """Submit test results to aggregator"""
    result_data = {
        "job_name": os.getenv("JOB_NAME", "integration-tests"),
        "test_suite": "integration",
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "duration_ms": duration_ms,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{TEST_RESULTS_URL}/api/v1/results",
                json=result_data,
                timeout=5.0
            )
            print(f"Results submitted: {passed} passed, {failed} failed")
        except Exception as e:
            print(f"Failed to submit results: {e}")
