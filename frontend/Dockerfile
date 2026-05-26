# Stage 1: Build Vue 3 app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy frontend source code
COPY . .

# Declare build arguments (can be passed via docker build --build-arg)
ARG VITE_API_BASE_URL=""
ARG VITE_API_CHAT_URL=""
ARG VITE_WS_CHAT_URL=""

# Inject build arguments into environment variables for Vite
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_CHAT_URL=$VITE_API_CHAT_URL
ENV VITE_WS_CHAT_URL=$VITE_WS_CHAT_URL

# Build Vue 3 app into static assets
RUN npm run build

# Stage 2: Serve static files using Nginx
FROM nginx:stable-alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build assets from Stage 1 to Nginx directory
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
