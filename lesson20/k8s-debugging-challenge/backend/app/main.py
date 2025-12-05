from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List
import os
import logging
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@database-service:5432/ecommerce")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Database models
class ProductDB(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock = Column(Integer)

# Pydantic models
class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int

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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Middleware for metrics
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
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("Backend service starting up...")
    db = SessionLocal()
    try:
        # Seed database with sample products
        if db.query(ProductDB).count() == 0:
            products = [
                ProductDB(name="Laptop Pro", price=1299.99, stock=15),
                ProductDB(name="Wireless Mouse", price=29.99, stock=50),
                ProductDB(name="Mechanical Keyboard", price=149.99, stock=30),
                ProductDB(name="USB-C Hub", price=49.99, stock=40),
                ProductDB(name="Monitor 27\"", price=399.99, stock=20),
                ProductDB(name="Webcam HD", price=79.99, stock=25),
            ]
            db.add_all(products)
            db.commit()
            logger.info("Database seeded with sample products")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "backend"}

@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check with database connectivity"""
    try:
        db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=503, detail="Database not available")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/products", response_model=List[Product])
async def get_products(db: Session = Depends(get_db)):
    """Get all products"""
    try:
        products = db.query(ProductDB).all()
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve products")

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    db_product = ProductDB(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    logger.info(f"Created product: {db_product.name}")
    return db_product

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "E-Commerce Backend API",
        "version": "1.0.0",
        "endpoints": ["/products", "/health", "/ready", "/metrics"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
