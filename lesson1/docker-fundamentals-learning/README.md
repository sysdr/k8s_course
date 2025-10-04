# Docker Fundamentals - Learning Environment

A comprehensive, production-ready Docker learning environment with practical examples covering containers, images, and Dockerfile best practices.

## 🎯 Learning Objectives

After completing these examples, you will:
- Understand the fundamental difference between containers and VMs
- Run pre-built production images (nginx, PostgreSQL)
- Write Dockerfiles following production best practices
- Implement multi-stage builds for optimized images
- Manage container networking and persistent storage
- Use Docker Compose for multi-container applications

## 📁 Project Structure

```
docker-fundamentals-learning/
├── 01-nginx-example/          # Running pre-built nginx container
├── 02-postgres-example/       # Stateful PostgreSQL container with volumes
├── 03-static-website/         # Building custom image for static site
├── 04-python-api/             # FastAPI application with dependencies
├── 05-multi-stage-build/      # Advanced multi-stage optimization
├── scripts/                   # Helper scripts for testing and cleanup
└── docs/                      # Additional learning materials
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed (version 20.10+)
- Basic command line knowledge
- 4GB free disk space

### Running the Examples

1. **Nginx Web Server (Pre-built Image)**
   ```bash
   cd 01-nginx-example
   ./run.sh
   # Visit http://localhost:8080
   ```

2. **PostgreSQL Database (Stateful Container)**
   ```bash
   cd 02-postgres-example
   ./run.sh
   # Connect: psql -h localhost -U devuser -d appdb
   ```

3. **Static Website (Custom Image)**
   ```bash
   cd 03-static-website
   ./build.sh
   ./run.sh
   # Visit http://localhost:3000
   ```

4. **Python FastAPI (Production Pattern)**
   ```bash
   cd 04-python-api
   docker-compose up --build
   # Visit http://localhost:8000/docs
   ```

5. **Multi-Stage Build (Advanced)**
   ```bash
   cd 05-multi-stage-build
   ./build.sh
   # Compare image sizes with docker images
   ```

## 📚 Learning Path

### Beginner Track
1. Start with `01-nginx-example` - Understand running containers
2. Move to `02-postgres-example` - Learn about volumes and persistence
3. Practice with `03-static-website` - Build your first image

### Intermediate Track
4. Study `04-python-api` - Production application patterns
5. Master `05-multi-stage-build` - Image optimization techniques

## 🔍 Key Concepts Covered

### Container vs VM
- Process isolation vs hardware virtualization
- Shared kernel architecture
- Startup time and resource efficiency

### Docker Images
- Layered filesystem architecture
- Image caching and build optimization
- Base image selection strategies

### Dockerfile Best Practices
- Dependency caching
- Multi-stage builds
- Security considerations
- Layer ordering optimization

### Container Networking
- Port mapping and exposure
- Container-to-container communication
- Network isolation

### Data Persistence
- Named volumes vs bind mounts
- Volume lifecycle management
- Database container patterns

## 🛠️ Helpful Commands

```bash
# List all containers
docker ps -a

# View container logs
docker logs <container-name>

# Execute command in running container
docker exec -it <container-name> sh

# View images
docker images

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# View resource usage
docker stats
```

## 🧹 Cleanup

To remove all containers, volumes, and images created by these examples:

```bash
./scripts/cleanup-all.sh
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080
# Or kill all containers
docker stop $(docker ps -aq)
```

### Build Failures
```bash
# Clear Docker cache
docker builder prune -a
# Rebuild without cache
docker build --no-cache -t myimage .
```

### Permission Errors
```bash
# Fix Docker socket permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

## 📖 Additional Resources

- [Docker Official Docs](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Hub](https://hub.docker.com/)

## 🎓 Next Steps

After mastering these fundamentals, proceed to:
- Image Optimization Techniques
- Docker Networking Deep Dive
- Docker Compose for Multi-Container Apps
- Introduction to Kubernetes

## 💡 Production Tips

1. **Never run as root** - Use USER instruction in Dockerfile
2. **Pin versions** - Always use specific image tags (e.g., `python:3.11-slim`)
3. **Scan for vulnerabilities** - Use `docker scan` or Trivy
4. **Minimize layers** - Combine RUN commands where appropriate
5. **Use .dockerignore** - Exclude unnecessary files from build context

---

**Happy Learning! 🐳**
