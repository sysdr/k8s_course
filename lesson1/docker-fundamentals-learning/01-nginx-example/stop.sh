#!/bin/bash

echo "🛑 Stopping nginx container..."
docker stop my-nginx
docker rm my-nginx
echo "✅ Container stopped and removed"
