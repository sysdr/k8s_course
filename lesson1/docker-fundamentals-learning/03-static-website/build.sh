#!/bin/bash

echo "🔨 Building static website Docker image..."

# Build the image
docker build -t static-website:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "Image details:"
    docker images static-website:latest
    echo ""
    echo "To run: ./run.sh"
else
    echo "❌ Build failed!"
    exit 1
fi
