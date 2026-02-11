FROM node:16-alpine as build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (including devDependencies needed for build)
RUN npm install --legacy-peer-deps && \
    npm install ajv@^8.12.0 --save-dev --legacy-peer-deps || true

# Copy source files
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json ./

# Build the application
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
