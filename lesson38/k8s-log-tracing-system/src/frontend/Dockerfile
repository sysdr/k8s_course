FROM node:20-alpine AS build
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps --no-audit --no-fund

# Copy all source files
COPY public ./public
COPY src ./src
COPY tsconfig.json ./

# Build the application
RUN npm run build

FROM nginx:1.25-alpine AS serve
COPY --from=build /app/build /usr/share/nginx/html
# rewrite all routes to index.html (SPA)
# Use docker-compose service name for local development, Kubernetes DNS for k8s
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/analytics/ { \
        rewrite ^/api/analytics/(.*) /$1 break; \
        proxy_pass http://analytics-service:8002; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    location /ws/ { \
        proxy_pass http://analytics-service:8002; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "Upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_read_timeout 86400; \
        proxy_send_timeout 86400; \
        proxy_connect_timeout 60; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
