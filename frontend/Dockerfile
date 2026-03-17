# 1. Dependencias
FROM node:20-slim AS deps
WORKDIR /app

# Install build dependencies for native modules
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm install --legacy-peer-deps

# 2. Constructor (Builder)
FROM node:20-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package*.json ./

# Copiar archivos de configuración CRÍTICOS para el build
COPY next.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./
COPY tsconfig.json ./

# Copiar código fuente
COPY middleware.ts ./
COPY app ./app
COPY components ./components
COPY hooks ./hooks
COPY lib ./lib
COPY store ./store
COPY types ./types
COPY public ./public

# Build de la aplicación
ENV NEXT_TELEMETRY_DISABLED 1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
RUN npm run build

# 3. Corredor (Runner) - Imagen final mínima
FROM node:20-slim AS runner
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
ENV PORT 3000
ENV HOSTNAME 0.0.0.0

# Copiar el servidor standalone
COPY --from=builder /app/.next/standalone ./

# COPIAR LOS ASSETS ESTÁTICOS (Paso crítico que faltaba)
COPY --from=builder /app/.next/static ./.next/static

# Copiar archivos públicos
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
