# Etapa 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar dependencias e instalar
COPY package.json package-lock.json ./
RUN npm install

# Copiar el código fuente y construir
COPY . .
RUN npm run build

# Etapa 2: Servir con Nginx
FROM nginx:alpine

# Copiar el build generado por Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de Nginx para SPA (React Router)
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
