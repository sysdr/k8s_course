# Example 1: Running Pre-Built Nginx Container

## Objective
Understand how to run pre-built images from Docker Hub and manage basic container operations.

## What You'll Learn
- Pulling images from registries
- Running containers in detached mode
- Port mapping for network access
- Container lifecycle management

## Architecture

```
Host Machine (port 8080)
    ↓
Docker Engine
    ↓
nginx Container (port 80)
    ↓
nginx process serving static files
```

## Quick Start

```bash
# Run nginx container
./run.sh

# Verify it's running
curl http://localhost:8080

# View logs
docker logs my-nginx

# Access container shell
docker exec -it my-nginx sh

# Stop container
./stop.sh
```

## Key Commands Explained

```bash
docker run -d -p 8080:80 --name my-nginx nginx:alpine
```

- `-d`: Detached mode (runs in background)
- `-p 8080:80`: Map host port 8080 to container port 80
- `--name my-nginx`: Give container a friendly name
- `nginx:alpine`: Image name and tag (Alpine is minimal base)

## Customization Exercise

1. Modify `custom-nginx.conf` to change server settings
2. Mount it into the container:
   ```bash
   docker run -d -p 8080:80 \
     -v $(pwd)/custom-nginx.conf:/etc/nginx/nginx.conf:ro \
     --name my-nginx nginx:alpine
   ```

## Production Considerations

- Always use specific tags (not `latest`)
- Implement health checks
- Configure proper logging
- Set resource limits

## Questions to Explore

1. What happens if you start the container without `-d`?
2. What's the difference between `nginx:alpine` and `nginx:latest`?
3. How do you view real-time logs?
4. What happens when you remove a running container?
