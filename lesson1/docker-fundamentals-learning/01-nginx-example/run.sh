#!/bin/bash

echo "🚀 Starting nginx container..."

# Stop and remove existing container if it exists
docker stop my-nginx 2>/dev/null || true
docker rm my-nginx 2>/dev/null || true

# Run nginx container
docker run -d \
  -p 8080:80 \
  --name my-nginx \
  nginx:alpine

echo "✅ Nginx container started!"
echo "🌐 Access at: http://localhost:8080"
echo ""
echo "Useful commands:"
echo "  docker logs my-nginx        # View logs"
echo "  docker exec -it my-nginx sh # Access shell"
echo "  docker stop my-nginx        # Stop container"
