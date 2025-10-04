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

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
