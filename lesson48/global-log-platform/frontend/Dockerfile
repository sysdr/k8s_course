FROM node:20-alpine AS builder
WORKDIR /app
ENV VITE_AGGREGATOR_WS=ws://localhost:8001/ws/logs
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
