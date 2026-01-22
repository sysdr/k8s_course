#!/usr/bin/env python3
"""
Test suite for Order Service
"""
import pytest
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "order-service"

def test_readiness_check():
    """Test readiness endpoint"""
    response = requests.get(f"{BASE_URL}/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"

def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    assert "orders_total" in response.text
    assert "order_processing_duration_seconds" in response.text

def test_create_order():
    """Test order creation"""
    order_data = {
        "customer_id": "TEST-123",
        "items": [
            {
                "product_id": "PROD-001",
                "quantity": 2,
                "price": 29.99,
                "category": "electronics"
            }
        ],
        "payment_method": "credit_card"
    }
    
    response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["status"] == "processing"
    assert data["total_amount"] == 59.98
    return data["order_id"]

def test_get_order():
    """Test retrieving an order"""
    # First create an order
    order_data = {
        "customer_id": "TEST-456",
        "items": [
            {
                "product_id": "PROD-002",
                "quantity": 1,
                "price": 49.99,
                "category": "clothing"
            }
        ],
        "payment_method": "debit_card"
    }
    
    create_response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    order_id = create_response.json()["order_id"]
    
    # Wait a bit for processing
    time.sleep(0.5)
    
    # Get the order
    response = requests.get(f"{BASE_URL}/api/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id

def test_list_orders():
    """Test listing orders"""
    response = requests.get(f"{BASE_URL}/api/orders?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_metrics_after_order():
    """Test that metrics are updated after creating orders"""
    # Get initial metrics
    initial_response = requests.get(f"{BASE_URL}/metrics")
    initial_text = initial_response.text
    
    # Create an order
    order_data = {
        "customer_id": "METRICS-TEST",
        "items": [
            {
                "product_id": "PROD-METRICS",
                "quantity": 1,
                "price": 99.99,
                "category": "books"
            }
        ],
        "payment_method": "paypal"
    }
    requests.post(f"{BASE_URL}/api/orders", json=order_data)
    
    # Wait for metrics to update
    time.sleep(1)
    
    # Check metrics again
    updated_response = requests.get(f"{BASE_URL}/metrics")
    updated_text = updated_response.text
    
    # Metrics should have changed
    assert updated_text != initial_text
    assert "orders_total" in updated_text

if __name__ == "__main__":
    print("Running Order Service tests...")
    print("Make sure the service is running on http://localhost:8000")
    
    try:
        test_health_check()
        print("✓ Health check passed")
        
        test_readiness_check()
        print("✓ Readiness check passed")
        
        test_metrics_endpoint()
        print("✓ Metrics endpoint passed")
        
        test_create_order()
        print("✓ Create order passed")
        
        test_get_order()
        print("✓ Get order passed")
        
        test_list_orders()
        print("✓ List orders passed")
        
        test_metrics_after_order()
        print("✓ Metrics update test passed")
        
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
