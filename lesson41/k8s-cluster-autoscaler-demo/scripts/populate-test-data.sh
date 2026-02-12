#!/bin/bash
set -euo pipefail

echo "Populating test data directly into Redis..."

# Get Redis pod name
REDIS_POD=$(kubectl get pod -n log-platform -l app=redis -o jsonpath='{.items[0].metadata.name}')

if [ -z "$REDIS_POD" ]; then
    echo "Error: Redis pod not found"
    exit 1
fi

# Test logs data
LOGS=(
    '{"timestamp":"2024-02-12T10:15:30Z","level":"INFO","service":"user-service","message":"User authentication successful for user_id: 12345"}'
    '{"timestamp":"2024-02-12T10:16:45Z","level":"ERROR","service":"payment-service","message":"Failed to process payment transaction. Error: Connection timeout to payment gateway after 30 seconds"}'
    '{"timestamp":"2024-02-12T10:17:20Z","level":"WARN","service":"database-service","message":"Connection pool usage at 85%. Consider scaling database connections."}'
    '{"timestamp":"2024-02-12T10:18:10Z","level":"DEBUG","service":"api-gateway","message":"Request received: GET /api/v1/users?page=1&limit=10, Processing time: 45ms"}'
    '{"timestamp":"2024-02-12T10:19:05Z","level":"ERROR","service":"email-service","message":"Failed to send email notification. SMTP server unreachable. Retry attempt 3/5"}'
    '{"timestamp":"2024-02-12T10:20:00Z","level":"INFO","service":"order-service","message":"Order #ORD-2024-001234 created successfully. Total amount: $299.99"}'
    '{"timestamp":"2024-02-12T10:21:15Z","level":"WARN","service":"cache-service","message":"Cache hit rate dropped to 65%. Performance may be impacted."}'
    '{"timestamp":"2024-02-12T10:22:30Z","level":"FATAL","service":"auth-service","message":"Critical: Database connection pool exhausted. Service unavailable."}'
)

echo "Adding logs to Redis..."

for log in "${LOGS[@]}"; do
    # Add to recent_logs list
    kubectl exec -n log-platform $REDIS_POD -- redis-cli LPUSH recent_logs "$log" > /dev/null
    
    # Extract level and add to error_logs if ERROR or FATAL
    level=$(echo "$log" | grep -o '"level":"[^"]*"' | cut -d'"' -f4)
    if [ "$level" = "ERROR" ] || [ "$level" = "FATAL" ]; then
        timestamp=$(echo "$log" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        score=$(date -d "$timestamp" +%s 2>/dev/null || echo $(date +%s))
        kubectl exec -n log-platform $REDIS_POD -- redis-cli ZADD error_logs $score "$log" > /dev/null
    fi
    
    # Update counters
    service=$(echo "$log" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)
    kubectl exec -n log-platform $REDIS_POD -- redis-cli HINCRBY "service:${service}:count" total 1 > /dev/null
    kubectl exec -n log-platform $REDIS_POD -- redis-cli HINCRBY "service:${service}:count" $level 1 > /dev/null
done

# Set total processed
kubectl exec -n log-platform $REDIS_POD -- redis-cli SET total_processed ${#LOGS[@]} > /dev/null

echo "Test data populated successfully!"
echo "Total logs added: ${#LOGS[@]}"
echo ""
echo "Refresh your dashboard at http://localhost:8080 to see the data"
