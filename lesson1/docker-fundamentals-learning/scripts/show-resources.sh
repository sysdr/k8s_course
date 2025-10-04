#!/bin/bash

echo "📊 Docker Resources Overview"
echo "============================"
echo ""

echo "🐳 Running Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "💾 Images:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"
echo ""

echo "📦 Volumes:"
docker volume ls
echo ""

echo "🌐 Networks:"
docker network ls
echo ""

echo "💡 Resource Usage:"
docker stats --no-stream
