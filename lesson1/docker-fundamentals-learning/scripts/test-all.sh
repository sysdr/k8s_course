#!/bin/bash

echo "🧪 Testing all Docker examples..."
echo "=================================="

# Test nginx
echo ""
echo "1️⃣ Testing nginx example..."
cd ../01-nginx-example
./run.sh
sleep 2
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Nginx test passed"
else
    echo "❌ Nginx test failed"
fi
./stop.sh

# Test postgres
echo ""
echo "2️⃣ Testing PostgreSQL example..."
cd ../02-postgres-example
./run.sh
sleep 5
if docker exec my-postgres psql -U devuser -d appdb -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL test passed"
else
    echo "❌ PostgreSQL test failed"
fi
./stop.sh

echo ""
echo "🎉 All tests complete!"
