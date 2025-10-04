# Example 3: Building a Custom Static Website Image

## Objective
Learn how to create custom Docker images using Dockerfile and understand the image build process.

## What You'll Learn
- Writing production-ready Dockerfiles
- Layer caching and build optimization
- COPY vs ADD instructions
- Health checks
- Custom nginx configuration

## Build and Run

```bash
# Build the image
./build.sh

# Run the container
./run.sh

# Visit http://localhost:3000
```

## Dockerfile Breakdown

```dockerfile
FROM nginx:alpine              # Start from minimal base
WORKDIR /usr/share/nginx/html  # Set working directory
RUN rm -rf ./*                 # Clean default files
COPY src/index.html .          # Copy application files
COPY nginx.conf /etc/nginx/    # Custom configuration
EXPOSE 80                      # Document port
HEALTHCHECK ...                # Container health monitoring
CMD ["nginx", "-g", "daemon off;"]  # Start command
```

## Layer Caching Exercise

1. Build the image once: `./build.sh`
2. Modify `src/index.html`
3. Rebuild: `./build.sh`
4. Notice which layers are cached vs rebuilt

## Optimization Challenge

Try to reduce build time by:
1. Reordering COPY commands
2. Combining RUN commands
3. Using .dockerignore file

## Production Considerations

- Pin nginx version (nginx:1.25-alpine)
- Minimize layers by combining commands
- Use .dockerignore to exclude unnecessary files
- Implement proper health checks
- Configure security headers
- Enable gzip compression
