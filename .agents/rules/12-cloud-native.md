# ☁️ Cloud Native & DevOps Baseline

> **Tipo**: `rule` | **Versión**: 3.6.0 | **Archivos**: `12-cloud-native.md`

## 📌 Filosofía 12-Factor App
Todo servicio o API construido bajo el framework LMAgent DEBE apuntar a complir con la metodología *12-Factor App*. 

1. **Codebase**: Un único repositorio bajo Git, múltiples deployments (Prod, Staging, Dev).
2. **Dependencies**: `package.json` o `requirements.txt` deben declarar *absolutamente todo*. Dependencias de sistema (`apt`) van aisladas en el Dockerfile.
3. **Configuraciones Extrinsecas**: NUNCA instancies o asumas credenciales en el código base. Usa `os.getenv` estricto (falla rápido si falta la variable).
4. **Stateless Processes**: El servidor web/API (FastAPI, Express, Go) debe ser 100% libre de estado local. Todo estado de sesión, descargas temporales o cachés deben delegarse a componentes de infraestructura atachables (S3, Redis, Memcached, Postgres).
5. **Disposable (Fast Startup / Graceful Shutdown)**: Configura manejadores de señales (SIGTERM, SIGINT) para drenar conexiones activas o rollbacks de DB antes de que el contenedor muera.

## 🐳 Contenedores Eficientes (Docker)

### Multi-Stage Builds
Usa siempre contenedores Multi-stage (*Builder* -> *Runtime*). Esto reduce la superficie de ataque y el tamaño drásticamente (ej: un node image que pasa de 1.2GB a una imagen alpine `distroless` de 90MB).

```dockerfile
# BUILDER
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# RUNTIME
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
# Dependencias en vivo UNICAMENTE
COPY --from=builder /app/node_modules ./node_modules 
CMD ["node", "dist/main.js"]
```

## ⚡ Diseños Serverless / Cero Escalado
Si se orquestan despliegues tipo AWS Lambda, Google Cloud Run o Vercel Edge:
- Minimiza el "Cold Start" evadiendo dependencias ultra-pesadas si no son absolutamente requeridas.
- En arquitecturas Functions, usa inyección o empaquetado *Tree-shaking* (esbuild, webpack) antes del subido a la nube.
