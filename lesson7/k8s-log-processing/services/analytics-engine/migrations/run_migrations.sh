#!/bin/bash
set -euo pipefail

echo "[MIGRATION] Starting database migrations..."

export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres-service}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-logs}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

# Wait for PostgreSQL to be ready
echo "[MIGRATION] Waiting for PostgreSQL..."
for i in {1..30}; do
    if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" &> /dev/null; then
        echo "[MIGRATION] PostgreSQL is ready"
        break
    fi
    echo "[MIGRATION] Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Run migrations
echo "[MIGRATION] Running migration scripts..."
for migration in /migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "[MIGRATION] Applying $(basename "$migration")..."
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration"
        echo "[MIGRATION] Applied $(basename "$migration") successfully"
    fi
done

echo "[MIGRATION] All migrations completed successfully"
