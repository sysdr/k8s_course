#!/bin/bash

set -euo pipefail

echo "Starting load test..."
echo "This will generate traffic to create logs in the system"

# Port forward API Gateway
kubectl port-forward -n logging-system svc/api-gateway 8000:8000 &
PF_PID=$!

sleep 3

echo "Generating load..."
for i in {1..100}; do
    curl -X POST http://localhost:8000/api/orders \
        -H "Content-Type: application/json" \
        -d '{
            "customer_id": "CUST-'$i'",
            "amount": '$((RANDOM % 1000 + 10))',
            "items": [
                {"product_id": "PROD-1", "quantity": 1, "price": 50.0}
            ],
            "payment_method": "credit_card"
        }' &
    
    if (( i % 10 == 0 )); then
        echo "Sent $i requests..."
        sleep 1
    fi
done

wait

echo "Load test complete!"
echo "Check Grafana for logs and metrics"

kill $PF_PID
