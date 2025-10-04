#!/bin/bash

echo "🛑 Stopping PostgreSQL container..."
docker stop my-postgres
docker rm my-postgres
echo "✅ Container stopped (volume preserved)"
echo "💾 Data remains in 'postgres-data' volume"
