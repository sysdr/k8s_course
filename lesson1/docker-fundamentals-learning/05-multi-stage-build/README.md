# Example 5: Multi-Stage Build Optimization

## Objective
Master multi-stage builds to create minimal, secure production images.

## What You'll Learn
- Single-stage vs multi-stage builds
- Image size optimization techniques
- Build cache strategies
- Production vs development images

## The Problem

Single-stage builds include everything needed to BUILD the application in the final image:
- Compilers and build tools
- Development dependencies
- Source code (sometimes unnecessary)
- Package manager caches

Result: 1GB+ images when you only need 100MB runtime.

## The Solution: Multi-Stage Builds

```dockerfile
# Stage 1: Build environment
FROM node:18 AS builder
COPY . .
RUN npm install && npm run build

# Stage 2: Production (clean slate)
FROM node:18-alpine
COPY --from=builder /build/dist ./dist
CMD ["node", "dist/app.js"]
```

Only the `COPY --from=builder` artifacts make it to the final image.

## Run the Comparison

```bash
./build.sh
```

This builds both versions and shows size comparison.

## Size Breakdown

**Single-Stage (1.2GB):**
- Base Node image: 900MB
- npm + node_modules: 200MB
- Build tools: 100MB

**Multi-Stage (150MB):**
- Alpine Node image: 50MB
- Production dependencies: 80MB
- Built application: 20MB

**Savings: 91% reduction**

## Real-World Impact

At scale with 1000 containers:
- Single-stage: 1.2TB storage, 10+ min pull times
- Multi-stage: 150GB storage, 30s pull times

Deployment speed increases 20x.

## Advanced Patterns

### 1. Multiple Build Stages

```dockerfile
FROM golang:1.21 AS builder
FROM node:18 AS frontend-builder
FROM nginx:alpine
COPY --from=builder /app/backend ./backend
COPY --from=frontend-builder /app/dist ./dist
```

### 2. Development vs Production

```dockerfile
FROM base AS development
RUN npm install

FROM base AS production
COPY --from=development /app/node_modules
```

### 3. Cache Optimization

```dockerfile
# Dependencies change rarely
COPY package*.json ./
RUN npm ci

# Code changes frequently
COPY src/ ./src/
RUN npm run build
```

## Exercise

Optimize the single-stage Dockerfile to:
1. Reduce image size by 80%+
2. Maintain all functionality
3. Implement proper caching

Compare your solution to the provided multi-stage example.
