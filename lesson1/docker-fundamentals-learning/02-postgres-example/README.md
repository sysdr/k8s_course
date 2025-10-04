# Example 2: PostgreSQL Container with Persistent Storage

## Objective
Learn how to run stateful containers with persistent volumes and understand data persistence patterns.

## What You'll Learn
- Volume management for data persistence
- Environment variable configuration
- Connecting to containerized databases
- Database initialization scripts

## Architecture

```
Host Machine
    ↓
Docker Volume (postgres-data)
    ↓
PostgreSQL Container
    ↓
PostgreSQL process with persisted data
```

## Quick Start

```bash
# Start PostgreSQL
./run.sh

# Connect to database
docker exec -it my-postgres psql -U devuser -d appdb

# Run queries
\dt          # List tables
\l           # List databases
SELECT version();

# Stop (data persists in volume)
./stop.sh

# Restart (data is still there!)
./run.sh
```

## Volume Persistence Test

```bash
# 1. Start PostgreSQL
./run.sh

# 2. Create test data
docker exec -it my-postgres psql -U devuser -d appdb -c \
  "CREATE TABLE test (id SERIAL PRIMARY KEY, name TEXT);"

docker exec -it my-postgres psql -U devuser -d appdb -c \
  "INSERT INTO test (name) VALUES ('Hello Docker');"

# 3. Stop and remove container
docker stop my-postgres
docker rm my-postgres

# 4. Start again
./run.sh

# 5. Verify data persists
docker exec -it my-postgres psql -U devuser -d appdb -c \
  "SELECT * FROM test;"
```

## Environment Variables

```bash
POSTGRES_USER=devuser       # Database user
POSTGRES_PASSWORD=devpass   # User password
POSTGRES_DB=appdb          # Initial database
```

## Production Considerations

- Never use default passwords in production
- Use secrets management (Docker secrets, Kubernetes secrets)
- Implement automated backups
- Monitor disk usage
- Configure connection pooling

## Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres-data

# Remove volume (⚠️ DELETES ALL DATA)
docker volume rm postgres-data
```
