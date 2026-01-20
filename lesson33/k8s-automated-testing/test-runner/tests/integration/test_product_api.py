import pytest
import httpx
import os

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

@pytest.mark.asyncio
async def test_product_crud_operations():
    """Test product CRUD operations"""
    async with httpx.AsyncClient() as client:
        # Create product
        new_product = {
            "id": "test-prod-999",
            "name": "Test Product",
            "description": "Test description",
            "price": 99.99,
            "stock": 100,
            "category": "test"
        }
        
        response = await client.post(
            f"{PRODUCT_SERVICE_URL}/api/v1/products",
            json=new_product
        )
        assert response.status_code == 201
        
        # Read product
        response = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products/test-prod-999")
        assert response.status_code == 200
        product = response.json()
        assert product["name"] == "Test Product"
        
        # Update product
        update_data = {"price": 79.99}
        response = await client.put(
            f"{PRODUCT_SERVICE_URL}/api/v1/products/test-prod-999",
            json=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["price"] == 79.99

@pytest.mark.asyncio
async def test_product_caching():
    """Test Redis caching for products"""
    async with httpx.AsyncClient() as client:
        # First request (cache miss)
        response1 = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products/prod-001")
        assert response1.status_code == 200
        
        # Second request (cache hit)
        response2 = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products/prod-001")
        assert response2.status_code == 200
        
        # Verify metrics show cache hits
        metrics_response = await client.get(f"{PRODUCT_SERVICE_URL}/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert int(metrics.get("cache_hits", 0)) > 0
