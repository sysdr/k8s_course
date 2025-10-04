#!/bin/bash

echo "🚀 Starting PostgreSQL container..."

# Stop and remove existing container
docker stop my-postgres 2>/dev/null || true
docker rm my-postgres 2>/dev/null || true

# Run PostgreSQL with persistent volume
docker run -d \
  --name my-postgres \
  -e POSTGRES_USER=devuser \
  -e POSTGRES_PASSWORD=devpass \
  -e POSTGRES_DB=appdb \
  -v postgres-data:/var/lib/postgresql/data \
  -p 5433:5432 \
  postgres:15-alpine

echo "✅ PostgreSQL started!"
echo "📊 Connection details:"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  User: devuser"
echo "  Password: devpass"
echo "  Database: appdb"
echo ""
echo "Connect with:"
echo "  docker exec -it my-postgres psql -U devuser -d appdb"
