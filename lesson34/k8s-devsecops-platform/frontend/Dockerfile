# Multi-stage build for optimized production image
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (need dev dependencies for build)
RUN npm install

# Copy source code
COPY public ./public
COPY src ./src

# Build application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Security: Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html && \
    mkdir -p /run/nginx && \
    chown -R nginx:nginx /run/nginx

# Copy built assets from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Note: Running as root for docker-compose simplicity
# In production, use proper volume mounts for /run/nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
