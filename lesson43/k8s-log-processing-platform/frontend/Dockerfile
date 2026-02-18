# Use static dashboard (no React build) for reliable Docker demo
FROM nginx:alpine
COPY static-dashboard.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
