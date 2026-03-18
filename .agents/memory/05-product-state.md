# Estado del Producto: Qubot V2 (Milenium Update)
**Última Actualización:** 18 de Marzo de 2026

## Visión General
Qubot V2 ha transitado por una reestructuración de 7 fases, evolucionando de un simple orquestador de agentes a un sistema "Mission Control" distribuido, seguro e inteligente, posicionándose a la par o por encima de alternativas como OpenClaw o NanoBot. 

La integración profunda con IA, su UI premium en React/NextJS y un backend orquestal en FastAPI con bases de datos asíncronas definen la arquitectura actual.

---

## Fases Completadas (Arquitectura Base y Features)

### 1. Sistema de Modelos Dinámicos (LLM Providers)
- Se integraron los modelos explícitos mediante el patrón Adapter / Strategy:
  - `OpenRouterProvider`
  - `AzureOpenAIProvider`
  - `DeepSeekProvider`
  - `CustomOpenAIProvider`
  - `OllamaProvider` (Ejecución local)
- Implementación de un `FailoverManager` para transferir ejecuciones entre modelos si falla el primario (ej. Rate Limits, caídas).

### 2. Canales de Comunicación (Inbound/Outbound)
- El subsistema `ChannelPlugin` procesa eventos asíncronos en back-end (FastAPI Startup Events):
  - **Slack**: Interceptación interactiva.
  - **Discord**: Verificación de firmas criptográficas (naclsal).
  - **WhatsApp**: Meta Graph API Webhooks.

### 3. Frontend Mission Control UI
- Estética glassmorphism y dark mode nativo mejorado con Tailwind/Lucide.
- Paneles reestructurados de métricas de agentes, visualización animada del ecosistema y control global de settings.
- Implementación del sistema dinámico de rutas en la App Router de Next.

### 4. Inteligencia de Agentes (Agent Intelligence)
- Integrada la herramienta iterativa de delegación inter-agente (`DelegateTool`) para jerarquías orquestales.
- Implementados los *Thinking Levels* para regular esfuerzo cognitivo en los prompts al vuelo.
- Memoria persistente PostgreSQL con soporte semántico inyectable en futuras expansiones de PGVector.

### 5. DevOps & Security
- El ecosistema corre integrado bajo un `docker-compose.yml` que empaqueta Backend, Frontend, Postgres, y Redis.
- Aislamiento robusto per-container para ejecución de *Tool Sandbox* contra ataques inyectivos en llamadas terminales.
- Script de diagnóstico `doctor.py` con logs ANSI customizado para prever malas prácticas de env y desconexiones de base de datos antes del deployment.

### 6. Ecosistema de Plataforma
- Arquitectura PWA con manifest (`manifest.ts`) para uso progresivo móvil/escritorio.
- `Skills Marketplace` desarrollado como un repositorio modular estilo "App Store" en el cual se activan dependencias de agentes (UI React Premium integrada con Zustand).

### 7. Seguridad y Autenticación (RBAC)
- Middleware de Login e implementación estricta de Base de Datos para tokens JWT generados via `passlib/bcrypt`.
- Distinción entre los Roles `ADMIN`, `USER`, y `VIEWER` atados al Session Storage.
- Rutas del Frontend encapsuladas en contexto seguro bajo el envoltorio `AuthProvider` global.

---

## ¿Qué falta implementar, corregir o mejorar? (Deuda Técnica / Roadmap)

### A. Mejoras de Backend / Infraestructura
1. **Migrations Automáticas (Alembic)**: 
   - Actualmente SQLAlchemy y SQLModel gestionan metadatos. Se requerirá un entorno de `alembic` bien estructurado para gestionar versiones de Base de Datos productivas sin pisar tablas existentes.
2. **Escalado Horizontal (Celery/KafKa)**:
   - Migrar la asignación pesada de workers de asyncio nativo a colas robustas estilo Celery/RabbitMQ o Redis Streams para distribuir procesos entre nodos múltiples si Qubot crece a miles de llamadas.
3. **Optimización de Postgres Vector**:
   - Falta activar explícitamente `pgvector` sobre los modelos de SQLAlchemy para habilitar Agent Memory contextual (Retrieval-Augmented Generation / RAG) a full escala.

### B. Mejoras de UI / UX (Frontend)
1. **Flow Builder Interactivo Completo**:
   - Profundizar el drag-and-drop de Nodos en la sección del Workflow visual usando librerías especializadas como React Flow.
2. **Gestión Total del Perfil de Usuario**:
   - Una pantalla `/settings/profile` dedicada para cambiar avatares, correos y contraseñas consumiendo las APIs que el router de Auth backend ya expone.
3. **Telemetría y Métricas WebSockets**:
   - Los dashboards asumen logs o datos por REST. Lo óptimo es abrir un canal WebSocket desde FastAPI que alimente logs del agent execution estatus "al vuelo" y lo pinte iterativamente en consolas del Frontend.

### C. Funcionalidades de Plataforma (Agentes)
1. **Marketplace Backend DB**:
   - El front simula las Skills como data estática / en memoria. Faltaría crear las tablas en DB y endpoints para instalar/borrar verdaderos empaquetados de plugins (plugins como scripts en python pre-renderizados) integrables con la ejecución al vuelo del orquestador.
2. **Local Model Caching**:
   - OllamaProvider actualmente dispara cada query in-memory. Manejar un TTL/caché de la capa LLM mejorará un 300% los tiempos de respuestas comunes.
