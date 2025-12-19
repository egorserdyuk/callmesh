FROM node:25-alpine AS builder

WORKDIR /app

# Copying package.json and installing all dependencies
COPY package*.json ./
RUN npm ci

# Copying the source code and building
COPY . .
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Removing the default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copying the assembled application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copying a custom nginx configuration for SPA
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
