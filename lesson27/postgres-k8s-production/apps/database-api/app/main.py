from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import asyncpg
import os
import time
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
DB_QUERY_DURATION = Histogram('db_query_duration_seconds', 'Database query duration', ['query_type'])
DB_CONNECTION_ERRORS = Counter('db_connection_errors_total', 'Total database connection errors')

app = FastAPI(title="Database API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime

class QueryLog(BaseModel):
    id: int
    user_id: Optional[int]
    query_text: str
    execution_time_ms: float
    rows_returned: int
    created_at: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime

# Database connection management
async def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'pgbouncer.database.svc.cluster.local'),
                port=int(os.getenv('DB_PORT', '5432')),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '#CHANGEME#'),
                database=os.getenv('DB_NAME', 'appdb'),
                min_size=5,
                max_size=20,
                command_timeout=60,
                ssl=False
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            DB_CONNECTION_ERRORS.inc()
            logger.error(f"Failed to create database pool: {e}")
            raise
    return db_pool

@app.on_event("startup")
async def startup():
    await get_db_pool()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    pool = await get_db_pool()
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/ready")
async def readiness_check():
    pool = await get_db_pool()
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM app.users")
        return {"status": "ready", "users_count": result}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Not ready")

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# User endpoints
@app.post("/users", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    start_time = time.time()
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                INSERT INTO app.users (username, email)
                VALUES ($1, $2)
                RETURNING id, username, email, created_at, updated_at
            """
            row = await conn.fetchrow(query, user.username, user.email)
            
            duration = time.time() - start_time
            DB_QUERY_DURATION.labels(query_type='insert').observe(duration)
            
            # Log query
            await conn.execute(
                """
                INSERT INTO app.queries (query_text, execution_time_ms, rows_returned)
                VALUES ($1, $2, $3)
                """,
                query, duration * 1000, 1
            )
            
            return User(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users", response_model=List[User])
async def list_users(skip: int = 0, limit: int = 100):
    start_time = time.time()
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id, username, email, created_at, updated_at
                FROM app.users
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, limit, skip)
            
            duration = time.time() - start_time
            DB_QUERY_DURATION.labels(query_type='select').observe(duration)
            
            return [User(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    start_time = time.time()
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id, username, email, created_at, updated_at
                FROM app.users
                WHERE id = $1
            """
            row = await conn.fetchrow(query, user_id)
            
            duration = time.time() - start_time
            DB_QUERY_DURATION.labels(query_type='select').observe(duration)
            
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            return User(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats/queries")
async def get_query_stats():
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    query_hash,
                    total_calls,
                    total_time,
                    min_time,
                    max_time,
                    mean_time,
                    COALESCE(stddev_time, 0) as stddev_time,
                    updated_at
                FROM analytics.query_stats
                ORDER BY total_time DESC
                LIMIT 20
            """
            rows = await conn.fetch(query)
            
            result = []
            for row in rows:
                result.append({
                    'query_hash': row['query_hash'],
                    'total_calls': row['total_calls'],
                    'total_time': float(row['total_time']) if row['total_time'] else 0.0,
                    'min_time': float(row['min_time']) if row['min_time'] else 0.0,
                    'max_time': float(row['max_time']) if row['max_time'] else 0.0,
                    'mean_time': float(row['mean_time']) if row['mean_time'] else 0.0,
                    'stddev_time': float(row['stddev_time']) if row['stddev_time'] else 0.0,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting query stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats/database")
async def get_database_stats():
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            stats = {}
            
            # Database size
            size_query = "SELECT pg_database_size('appdb') as size"
            stats['database_size'] = await conn.fetchval(size_query)
            
            # Connection count
            conn_query = "SELECT count(*) FROM pg_stat_activity WHERE datname = 'appdb'"
            stats['active_connections'] = await conn.fetchval(conn_query)
            
            # Transaction stats
            tx_query = """
                SELECT 
                    xact_commit as commits,
                    xact_rollback as rollbacks,
                    blks_read as blocks_read,
                    blks_hit as blocks_hit
                FROM pg_stat_database
                WHERE datname = 'appdb'
            """
            tx_stats = await conn.fetchrow(tx_query)
            stats['transactions'] = dict(tx_stats)
            
            return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
