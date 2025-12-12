# Build stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY public ./public
COPY src ./src

RUN npm run build

# Production stage
FROM nginx:alpine

# Create non-root user
RUN addgroup -g 10001 -S appuser && adduser -u 10001 -S appuser -G appuser

# Copy nginx configuration
COPY --chown=appuser:appuser nginx.conf /etc/nginx/nginx.conf

# Copy built assets
COPY --from=build --chown=appuser:appuser /app/build /usr/share/nginx/html

# Switch to non-root user
USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
