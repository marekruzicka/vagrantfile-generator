# syntax=docker/dockerfile:1

FROM node:18-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

FROM nginx:stable-alpine AS runtime
WORKDIR /usr/share/nginx/html

COPY --from=build /app/dist/ ./
COPY --from=build /app/src/views ./views
COPY --from=build /app/src/components ./components
COPY --from=build /app/src/modals ./modals
COPY --from=build /app/src/js ./js
COPY --from=build /app/src/styles ./styles
COPY --from=build /app/src/public ./

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.d/50-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/50-runtime-config.sh

# Create non-root user and directories with proper permissions
RUN addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup \
    && mkdir -p /var/cache/nginx /var/log/nginx \
    && chown -R appuser:appgroup /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx \
    && chmod -R 755 /var/cache/nginx /var/log/nginx

# Update nginx.conf to use /tmp for pid file (world-writable, works for non-root)
RUN sed -i 's|pid.*|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Switch to non-root user
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1
