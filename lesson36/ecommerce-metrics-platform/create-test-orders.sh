#!/bin/bash
# Create test orders to populate the dashboard

for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/orders \
    -H "Content-Type: application/json" \
    -d "{
      \"customer_id\": \"TEST-$i\",
      \"items\": [{
        \"product_id\": \"PROD-$i\",
        \"quantity\": 1,
        \"price\": $(($RANDOM % 500 + 10)).99,
        \"category\": \"electronics\"
      }],
      \"payment_method\": \"credit_card\"
    }" > /dev/null
  echo "Order $i created"
  sleep 0.3
done

echo ""
echo "Waiting for orders to process..."
sleep 5
echo ""
echo "Current metrics:"
curl -s http://localhost:8000/api/metrics | python3 -m json.tool
