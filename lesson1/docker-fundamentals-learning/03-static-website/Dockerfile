# Example: Building a custom Docker image for a static website
# This demonstrates Dockerfile basics and layer caching

FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy static website files
# Note: Each COPY creates a new layer
COPY src/index.html .
COPY src/css/ ./css/
COPY src/js/ ./js/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
