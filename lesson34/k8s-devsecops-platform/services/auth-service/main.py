"""
Authentication Service - JWT token generation and validation
Implements secure password hashing and token management
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
import logging
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
AUTH_ATTEMPTS = Counter('auth_attempts_total', 'Authentication attempts', ['status'])
TOKEN_VALIDATIONS = Counter('token_validations_total', 'Token validations', ['status'])

app = FastAPI(title="Authentication Service")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insecure-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))

# In-memory user store (use database in production)
users_db = {
    "admin": {
        "username": "admin",
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()),
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password_hash": bcrypt.hashpw("user123".encode(), bcrypt.gensalt()),
        "role": "user"
    }
}

class AuthRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    role: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generate JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/login", response_model=TokenResponse)
async def login(auth_req: AuthRequest):
    """Authenticate user and return JWT token"""
    logger.info(f"Login attempt for user: {auth_req.username}")
    
    user = users_db.get(auth_req.username)
    
    if not user or not verify_password(auth_req.password, user["password_hash"]):
        AUTH_ATTEMPTS.labels(status='failed').inc()
        logger.warning(f"Failed login attempt for user: {auth_req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    AUTH_ATTEMPTS.labels(status='success').inc()
    logger.info(f"Successful login for user: {auth_req.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )

@app.post("/verify")
async def verify_token(token_req: TokenRequest):
    """Verify JWT token validity"""
    try:
        payload = jwt.decode(token_req.token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            TOKEN_VALIDATIONS.labels(status='invalid').inc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        TOKEN_VALIDATIONS.labels(status='valid').inc()
        return TokenData(username=username, role=role)
        
    except jwt.ExpiredSignatureError:
        TOKEN_VALIDATIONS.labels(status='expired').inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        TOKEN_VALIDATIONS.labels(status='invalid').inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
