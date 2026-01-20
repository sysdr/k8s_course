import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")

@pytest.fixture
def driver():
    """Setup Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
    
    yield driver
    driver.quit()

def test_product_browsing(driver):
    """Test user can browse products"""
    driver.get(FRONTEND_URL)
    
    # Wait for products to load
    wait = WebDriverWait(driver, 10)
    products = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
    )
    
    assert len(products) > 0, "No products displayed"

def test_order_placement(driver):
    """Test complete order placement flow"""
    driver.get(FRONTEND_URL)
    
    wait = WebDriverWait(driver, 10)
    
    # Click first product
    first_product = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "product-card"))
    )
    first_product.click()
    
    # Add to cart
    add_to_cart_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "add-to-cart"))
    )
    add_to_cart_btn.click()
    
    # Proceed to checkout
    checkout_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "checkout"))
    )
    checkout_btn.click()
    
    # Verify order confirmation
    confirmation = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "order-confirmation"))
    )
    
    assert "Order placed successfully" in confirmation.text
