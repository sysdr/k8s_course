FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY public/ ./public/
COPY src/ ./src/

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
