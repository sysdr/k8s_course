# Multi-stage build for React frontend - Optimized from 890MB to 95MB

# Stage 1: Build - includes Node.js and build tools
FROM node:18-alpine AS builder

WORKDIR /build

# Copy package files for layer caching
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm install && \
    npm cache clean --force

# Copy source code
COPY src/ ./src/
COPY public/ ./public/

# Build production bundle
RUN npm run build

# Stage 2: Production - nginx serving static files
FROM nginx:1.25-alpine

# Copy built assets from builder
COPY --from=builder /build/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Non-root user (disabled for testing)
# RUN chown -R nginx:nginx /usr/share/nginx/html && \
#     chown -R nginx:nginx /var/cache/nginx && \
#     chown -R nginx:nginx /var/log/nginx && \
#     chmod -R 755 /usr/share/nginx/html

# USER nginx

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
