from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
import logging
import redis
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ecommerce:password@postgres-svc:5432/ecommerce")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-svc:6379/0")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis client
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request latency')

# Database model
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    category = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="E-Commerce Backend API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.observe(duration)
    
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "backend-api",
        "version": "1.0.0"
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "not_configured"
    
    logger.info(f"Health check: {health_status['status']}")
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    logger.info(f"Fetching products: skip={skip}, limit={limit}, category={category}")
    
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    logger.info(f"Returning {len(products)} products")
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    logger.info(f"Fetching product: id={product_id}")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        logger.warning(f"Product not found: id={product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@app.post("/api/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    logger.info(f"Creating product: {product.name}")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    logger.info(f"Product created: id={db_product.id}")
    return db_product

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get inventory statistics"""
    total_products = db.query(Product).count()
    total_value = db.query(Product).with_entities(
        db.func.sum(Product.price * Product.stock)
    ).scalar() or 0
    
    categories = db.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()
    
    stats = {
        "total_products": total_products,
        "total_inventory_value": float(total_value),
        "categories": [{"name": cat, "count": count} for cat, count in categories],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Stats generated: {total_products} products")
    return stats

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "E-Commerce Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "products": "/api/products",
            "stats": "/api/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
