# ---------------------------------------------------------------------------
# FRONTEND DOCKERFILE (multi-stage build)
# ---------------------------------------------------------------------------
# Stage 1: Build the React application with Node.js.
# Stage 2: Serve the built files with a lightweight nginx container.
#
# Multi-stage builds keep the final image small (~25 MB) by discarding
# all Node.js build tooling after the build completes.

# ---------------------------------------------------------------------------
# STAGE 1 — Build the React app
# ---------------------------------------------------------------------------
# node:20-alpine is a minimal Node.js 20 image based on Alpine Linux.
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first (layer caching optimization).
# Docker caches this layer; if package.json hasn't changed, npm ci is reused.
COPY package.json package-lock.json ./

# npm ci installs exact versions from package-lock.json (faster than npm install).
RUN npm ci

# Copy the rest of the source code and build the production bundle.
COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# STAGE 2 — Serve with nginx
# ---------------------------------------------------------------------------
# nginx:alpine is the official nginx image on Alpine Linux (~25 MB).
FROM nginx:alpine

# Copy the built static files from Stage 1 into nginx's document root.
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom nginx config (proxies /api/* to the backend).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Document the port nginx listens on (matches nginx.conf listen directive).
EXPOSE 80

# Start nginx in the foreground (daemon off keeps the container running).
CMD ["nginx", "-g", "daemon off;"]
