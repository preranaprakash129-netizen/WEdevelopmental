# Stage 1: install deps and build static assets.
# VITE_USE_MOCKS is inlined into the JS bundle at build time (import.meta.env),
# so it must be a build ARG, not just a runtime environment variable.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_USE_MOCKS=false
ENV VITE_USE_MOCKS=$VITE_USE_MOCKS
RUN npm run build

# Stage 2: serve the built assets and proxy /api to backend-api over the compose network.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 5173
