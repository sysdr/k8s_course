# Docker Command Reference

## Container Lifecycle

```bash
# Run container
docker run -d --name myapp -p 8080:80 nginx

# Stop container
docker stop myapp

# Start stopped container
docker start myapp

# Restart container
docker restart myapp

# Remove container
docker rm myapp

# Force remove running container
docker rm -f myapp
```

## Images

```bash
# List images
docker images

# Pull image
docker pull nginx:alpine

# Build image
docker build -t myapp:v1 .

# Remove image
docker rmi myapp:v1

# Tag image
docker tag myapp:v1 myapp:latest

# Push to registry
docker push myregistry/myapp:v1
```

## Inspection & Debugging

```bash
# View container logs
docker logs myapp
docker logs -f myapp  # Follow logs

# Execute command in container
docker exec -it myapp sh

# Inspect container
docker inspect myapp

# View resource usage
docker stats

# View container processes
docker top myapp
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

## Volumes

```bash
# Create volume
docker volume create mydata

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata

# Mount volume
docker run -v mydata:/data myapp
```

## Networks

```bash
# List networks
docker network ls

# Create network
docker network create mynet

# Connect container to network
docker network connect mynet myapp

# Inspect network
docker network inspect mynet
```

## Docker Compose

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and restart
docker-compose up --build
```
