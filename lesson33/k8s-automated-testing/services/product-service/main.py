from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import redis
import json
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Models
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category: str
    created_at: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None

# In-memory database (for demo - would use PostgreSQL in production)
products_db = {
    "prod-001": Product(
        id="prod-001",
        name="Laptop Pro",
        description="High-performance laptop",
        price=1299.99,
        stock=50,
        category="electronics",
        created_at=datetime.utcnow().isoformat()
    ),
    "prod-002": Product(
        id="prod-002",
        name="Wireless Mouse",
        description="Ergonomic wireless mouse",
        price=29.99,
        stock=200,
        category="electronics",
        created_at=datetime.utcnow().isoformat()
    ),
}

# Cache product in Redis
def cache_product(product: Product):
    try:
        redis_client.setex(
            f"product:{product.id}",
            3600,  # 1 hour TTL
            product.json()
        )
    except Exception as e:
        logger.error(f"Redis cache error: {e}")

# Get product from cache
def get_cached_product(product_id: str) -> Optional[Product]:
    try:
        cached = redis_client.get(f"product:{product_id}")
        if cached:
            return Product.parse_raw(cached)
    except Exception as e:
        logger.error(f"Redis fetch error: {e}")
    return None

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Readiness check - service is ready to accept traffic"""
    return {"status": "ready", "products_count": len(products_db)}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    product_count = len(products_db)
    return {
        "products_total": product_count,
        "cache_hits": redis_client.get("cache_hits") or 0,
        "cache_misses": redis_client.get("cache_misses") or 0
    }

@app.get("/api/v1/products", response_model=List[Product])
async def list_products(category: Optional[str] = None):
    """List all products or filter by category"""
    products = list(products_db.values())
    
    if category:
        products = [p for p in products if p.category == category]
    
    logger.info(f"Listed {len(products)} products")
    return products

@app.get("/api/v1/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get product by ID with Redis caching"""
    # Try cache first
    cached_product = get_cached_product(product_id)
    if cached_product:
        redis_client.incr("cache_hits")
        logger.info(f"Cache hit for product {product_id}")
        return cached_product
    
    redis_client.incr("cache_misses")
    
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    cache_product(product)
    
    return product

@app.post("/api/v1/products", response_model=Product, status_code=201)
async def create_product(product: Product):
    """Create a new product"""
    if product.id in products_db:
        raise HTTPException(status_code=409, detail="Product already exists")
    
    product.created_at = datetime.utcnow().isoformat()
    products_db[product.id] = product
    cache_product(product)
    
    logger.info(f"Created product {product.id}")
    return product

@app.put("/api/v1/products/{product_id}", response_model=Product)
async def update_product(product_id: str, update: ProductUpdate):
    """Update product details"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    
    # Update fields
    if update.name is not None:
        product.name = update.name
    if update.description is not None:
        product.description = update.description
    if update.price is not None:
        product.price = update.price
    if update.stock is not None:
        product.stock = update.stock
    if update.category is not None:
        product.category = update.category
    
    cache_product(product)
    logger.info(f"Updated product {product_id}")
    
    return product

@app.post("/api/v1/products/{product_id}/reserve")
async def reserve_stock(product_id: str, quantity: int):
    """Reserve product stock for order - called by order service"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    
    if product.stock < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    product.stock -= quantity
    cache_product(product)
    
    logger.info(f"Reserved {quantity} units of product {product_id}")
    return {"reserved": quantity, "remaining_stock": product.stock}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
