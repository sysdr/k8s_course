from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import time

app = FastAPI(
    title="Docker Learning API",
    description="A sample FastAPI application running in Docker",
    version="1.0.0"
)

# In-memory data store
items_db = []

class Item(BaseModel):
    id: int
    name: str
    description: str = None
    price: float

@app.get("/")
async def root():
    return {
        "message": "Welcome to Docker Learning API",
        "container": "This API is running in a Docker container",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "items": "/items"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

@app.get("/container-info")
async def container_info():
    import os
    import platform
    
    return {
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "working_directory": os.getcwd()
    }
