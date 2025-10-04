#!/bin/bash

echo "🚀 Starting static website container..."

# Stop and remove existing container
docker stop static-website 2>/dev/null || true
docker rm static-website 2>/dev/null || true

# Run the container
docker run -d \
  -p 3000:80 \
  --name static-website \
  static-website:latest

echo "✅ Website is running!"
echo "🌐 Access at: http://localhost:3000"
echo ""
echo "Useful commands:"
echo "  docker logs static-website           # View logs"
echo "  docker exec -it static-website sh    # Access shell"
echo "  docker stop static-website           # Stop container"
