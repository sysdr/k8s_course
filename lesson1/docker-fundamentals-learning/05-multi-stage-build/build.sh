#!/bin/bash

echo "🔨 Building both single-stage and multi-stage images..."
echo ""

# Build single-stage
echo "1️⃣ Building single-stage image..."
docker build -f Dockerfile.single-stage -t demo:single-stage .

# Build multi-stage
echo ""
echo "2️⃣ Building multi-stage image..."
docker build -f Dockerfile.multi-stage -t demo:multi-stage .

echo ""
echo "📊 Image Size Comparison:"
echo "=========================="
docker images | grep demo

echo ""
echo "💡 Notice the size difference!"
echo "Single-stage: ~1GB (includes build tools)"
echo "Multi-stage: ~150MB (only runtime needed)"
