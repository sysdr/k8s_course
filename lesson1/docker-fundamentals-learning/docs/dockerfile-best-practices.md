# Dockerfile Best Practices

## 1. Order Matters (Caching)

❌ Bad:
```dockerfile
FROM node:18
COPY . .
RUN npm install
```

✅ Good:
```dockerfile
FROM node:18
COPY package*.json ./
RUN npm install
COPY . .
```

**Why:** Dependencies change less frequently than code. This order maximizes cache hits.

## 2. Use Specific Tags

❌ Bad:
```dockerfile
FROM python:latest
```

✅ Good:
```dockerfile
FROM python:3.11-slim
```

**Why:** `latest` changes over time, breaking reproducibility.

## 3. Multi-Stage Builds

❌ Bad:
```dockerfile
FROM node:18
RUN npm install && npm run build
CMD ["node", "dist/app.js"]
```

✅ Good:
```dockerfile
FROM node:18 AS builder
RUN npm install && npm run build

FROM node:18-alpine
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/app.js"]
```

**Why:** Reduces final image size by 80-90%.

## 4. Run as Non-Root

❌ Bad:
```dockerfile
CMD ["node", "app.js"]
```

✅ Good:
```dockerfile
RUN useradd -m appuser
USER appuser
CMD ["node", "app.js"]
```

**Why:** Security. Container escapes are less dangerous without root.

## 5. Use .dockerignore

Create `.dockerignore`:
```
node_modules
.git
*.md
.env
```

**Why:** Smaller build context = faster builds.

## 6. Combine RUN Commands

❌ Bad:
```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean
```

✅ Good:
```dockerfile
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

**Why:** Each RUN creates a layer. Fewer layers = smaller image.

## 7. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost/ || exit 1
```

**Why:** Container orchestrators can detect and restart unhealthy containers.

## 8. Use COPY Over ADD

✅ Prefer:
```dockerfile
COPY src/ /app/src/
```

❌ Avoid (unless needed):
```dockerfile
ADD https://example.com/file.tar.gz /tmp/
```

**Why:** COPY is explicit. ADD has implicit behaviors (auto-extraction).

## 9. Leverage Build Cache

```dockerfile
# These change rarely
COPY package.json package-lock.json ./
RUN npm ci

# These change often
COPY src/ ./src/
```

## 10. Security Scanning

```bash
# Scan for vulnerabilities
docker scan myimage:latest

# Or use Trivy
trivy image myimage:latest
```
