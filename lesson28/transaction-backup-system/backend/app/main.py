"""
Critical Transaction Processing System
Demonstrates production backup/restore patterns with stateful data
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from contextlib import asynccontextmanager
from starlette.responses import Response
from sqlalchemy import func
from datetime import datetime, timedelta
import logging
import time
from typing import List, Optional
import os
import subprocess
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.core.database import engine, get_db, Base
from app.core.redis_client import get_redis_client
from app.models.transaction import Transaction as TransactionModel
from app.api.schemas import TransactionCreate, TransactionResponse, TransactionStats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
transaction_counter = Counter(
    'transactions_total', 
    'Total number of transactions processed',
    ['status']
)
transaction_duration = Histogram(
    'transaction_duration_seconds',
    'Transaction processing duration'
)
backup_data_size = Counter(
    'backup_data_size_bytes',
    'Total size of data requiring backup'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Transaction system started successfully")
    yield
    # Shutdown
    logger.info("Shutting down transaction system")

app = FastAPI(
    title="Critical Transaction System",
    description="Production system demonstrating backup/restore patterns",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Kubernetes liveness probe"""
    return {"status": "healthy", "service": "transaction-api"}

@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe - verifies database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new financial transaction (critical data requiring backup)"""
    start_time = time.time()
    
    try:
        # Create transaction in database
        db_transaction = TransactionModel(
            user_id=transaction.user_id,
            amount=transaction.amount,
            currency=transaction.currency,
            transaction_type=transaction.transaction_type,
            description=transaction.description,
            status="completed"
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # Update metrics
        transaction_counter.labels(status="success").inc()
        backup_data_size.inc(len(str(db_transaction.__dict__)))
        
        # Cache in Redis for performance
        redis_client = get_redis_client()
        if redis_client:
            cache_key = f"transaction:{db_transaction.id}"
            redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                str(db_transaction.__dict__)
            )
        
        duration = time.time() - start_time
        transaction_duration.observe(duration)
        
        logger.info(f"Transaction created: {db_transaction.id} (${transaction.amount})")
        
        return TransactionResponse(
            id=db_transaction.id,
            user_id=db_transaction.user_id,
            amount=db_transaction.amount,
            currency=db_transaction.currency,
            transaction_type=db_transaction.transaction_type,
            description=db_transaction.description,
            status=db_transaction.status,
            created_at=db_transaction.created_at
        )
        
    except Exception as e:
        db.rollback()
        transaction_counter.labels(status="error").inc()
        logger.error(f"Transaction creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )

@app.get("/api/v1/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List transactions with pagination"""
    query = db.query(TransactionModel)
    
    if user_id:
        query = query.filter(TransactionModel.user_id == user_id)
    
    transactions = query.offset(skip).limit(limit).all()
    
    return [
        TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            amount=t.amount,
            currency=t.currency,
            transaction_type=t.transaction_type,
            description=t.description,
            status=t.status,
            created_at=t.created_at
        )
        for t in transactions
    ]

@app.get("/api/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get specific transaction by ID"""
    # Try cache first
    redis_client = get_redis_client()
    if redis_client:
        cache_key = f"transaction:{transaction_id}"
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for transaction {transaction_id}")
    
    transaction = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    return TransactionResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        transaction_type=transaction.transaction_type,
        description=transaction.description,
        status=transaction.status,
        created_at=transaction.created_at
    )

@app.get("/api/v1/stats", response_model=TransactionStats)
async def get_stats(db: Session = Depends(get_db)):
    """Get transaction statistics (critical for backup validation)"""
    total = db.query(TransactionModel).count()
    
    total_volume = db.query(
        func.sum(TransactionModel.amount)
    ).scalar() or 0.0
    
    recent_count = db.query(TransactionModel).filter(
        TransactionModel.created_at >= datetime.utcnow() - timedelta(hours=1)
    ).count()
    
    return TransactionStats(
        total_transactions=total,
        total_volume=float(total_volume),
        recent_transactions_1h=recent_count,
        last_backup_size=total * 500  # Approximate bytes per transaction
    )

@app.delete("/api/v1/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Delete transaction (demonstrates why backups matter!)"""
    transaction = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    db.delete(transaction)
    db.commit()
    
    # Clear cache
    redis_client = get_redis_client()
    if redis_client:
        redis_client.delete(f"transaction:{transaction_id}")
    
    logger.warning(f"Transaction deleted: {transaction_id} - This data loss is recoverable from backup!")
    
    return {"message": "Transaction deleted", "id": transaction_id}

@app.post("/api/v1/backup")
async def create_backup():
    """Trigger a Velero backup of the transaction system"""
    try:
        backup_name = f"manual-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Load Kubernetes config (in-cluster or from kubeconfig)
        try:
            config.load_incluster_config()
        except:
            try:
                config.load_kube_config()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Cannot load Kubernetes config: {str(e)}"
                )
        
        # Create Velero Backup CRD using Kubernetes API
        custom_api = client.CustomObjectsApi()
        
        backup_body = {
            "apiVersion": "velero.io/v1",
            "kind": "Backup",
            "metadata": {
                "name": backup_name,
                "namespace": "velero"
            },
            "spec": {
                "includedNamespaces": ["transaction-system"],
                "defaultVolumesToRestic": True,
                "storageLocation": "default",
                "volumeSnapshotLocations": ["default"],
                "ttl": "720h0m0s"  # 30 days
            }
        }
        
        try:
            custom_api.create_namespaced_custom_object(
                group="velero.io",
                version="v1",
                namespace="velero",
                plural="backups",
                body=backup_body
            )
            logger.info(f"Backup CRD created successfully: {backup_name}")
            return {
                "status": "success",
                "message": f"Backup created: {backup_name}. It will run asynchronously.",
                "backup_name": backup_name
            }
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Velero CRDs not found. Please install Velero first."
                )
            else:
                logger.error(f"Backup creation failed: {e.reason}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Backup creation failed: {e.reason}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@app.post("/api/v1/restore")
async def restore_backup(backup_name: Optional[str] = None):
    """Restore from a Velero backup"""
    try:
        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except:
            try:
                config.load_kube_config()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Cannot load Kubernetes config: {str(e)}"
                )
        
        custom_api = client.CustomObjectsApi()
        
        # If no backup name provided, get the latest backup
        if not backup_name:
            try:
                backups = custom_api.list_namespaced_custom_object(
                    group="velero.io",
                    version="v1",
                    namespace="velero",
                    plural="backups"
                )
                
                if not backups.get("items"):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No backups found"
                    )
                
                # Get the most recent backup
                items = backups["items"]
                items.sort(key=lambda x: x.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
                backup_name = items[0]["metadata"]["name"]
            except ApiException as e:
                if e.status == 404:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Velero CRDs not found. Please install Velero first."
                    )
                raise
        
        restore_name = f"restore-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Create Velero Restore CRD
        restore_body = {
            "apiVersion": "velero.io/v1",
            "kind": "Restore",
            "metadata": {
                "name": restore_name,
                "namespace": "velero"
            },
            "spec": {
                "backupName": backup_name,
                "includedNamespaces": ["transaction-system"]
            }
        }
        
        try:
            custom_api.create_namespaced_custom_object(
                group="velero.io",
                version="v1",
                namespace="velero",
                plural="restores",
                body=restore_body
            )
            logger.info(f"Restore CRD created successfully: {restore_name} from {backup_name}")
            return {
                "status": "success",
                "message": f"Restore initiated: {restore_name}. It will run asynchronously.",
                "restore_name": restore_name,
                "backup_name": backup_name
            }
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Velero CRDs not found. Please install Velero first."
                )
            else:
                logger.error(f"Restore creation failed: {e.reason}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Restore creation failed: {e.reason}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore: {str(e)}"
        )
