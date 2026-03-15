# Persona Mapping — Guía Completa de las 21 Personas

> Referencia rápida para que el Orchestrator sepa exactamente qué persona activar según el contexto.

## Mapa de Personas por Categoría

### 🔧 Engineering (Implementación)

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| Backend Engineer | `/dev` | FastAPI, NestJS, APIs, SQL | Implementación de lógica de negocio y APIs |
| Frontend Engineer | `/frontend` | React, Next.js, TypeScript | Interfaces de usuario, componentes, UX |
| Mobile Engineer | `/mobile` | React Native, Expo | Apps móviles iOS/Android |
| DevOps Engineer | `/devops` | Docker, CI/CD, K8s | Infraestructura, deployments, pipelines |
| Data Engineer | `/dba` | PostgreSQL, SQL, migraciones | Schemas, queries, backups, optimización DB |
| Performance Engineer | `/perf` | Profiling, caching, load testing | Optimización de rendimiento, bottlenecks |

### 🛡️ Quality & Security

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| QA Engineer | `/qa` | pytest, jest, Playwright, Evals | Testing, coverage, validación de calidad |
| Security Analyst | `/sec` | OWASP, auth, encryption | Auditorías de seguridad, threat modeling |

### 🧠 Intelligence & Automation

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| AI Agent Engineer | `/ai` | LLM agents, ReAct, MCP | Diseño de agentes de IA |
| Prompt Engineer | `/prompt` | CoT, DSPy, Evals | Optimización de prompts y system prompts |
| Automation Engineer | `/auto` | n8n, webhooks, ETL | Automatizaciones y flujos de trabajo |

### 📋 Strategy & Management

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| Product Manager | `/pm` | PRDs, user stories, RICE | Requisitos, priorización, roadmap |
| Architect | `/arch` | C4, ADRs, system design | Diseño de sistemas, decisiones técnicas |
| Tech Lead | `/lead` | Code review, tech debt, DORA | Liderazgo técnico, mentoring |
| Scrum Master | `/sm` | Agile, Kanban, retrospectives | Ceremonias, métricas de equipo |

### 📝 Communication & Design

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| Technical Writer | `/writer` | READMEs, API docs, changelogs | Documentación técnica |
| UX/UI Designer | `/ux` | Design systems, WCAG, prototyping | Diseño de interfaces y experiencia |

### 🧪 Methodologies (Nuevas v3.0)

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| BMAD Methodology | `/bmad` | Scale-Adaptive Intelligence, Levels 0-4 | Clasificación de complejidad, kickoff de proyecto |
| SWE-Agent | `/swe` | Trajectory logging, Edit-Lint-Test | Resolución autónoma de issues |
| Spec-Driven Dev | `/spec-dev` | SPECIFY→PLAN→TASKS→IMPLEMENT→VERIFY | Features Level 2+ que necesitan spec formal |

### 🎯 Meta

| Persona | Trigger | Expertise Principal | Cuándo Activar |
|---------|---------|--------------------|--------------
| Orchestrator | `/orch` | Routing, coordination, handoff | Cuando no está claro quién debe actuar |

## Reglas de Combinación

### Combinaciones Frecuentes

| Escenario | Personas | Orden |
|-----------|----------|-------|
| Feature nueva completa | PM → Arch → Dev → QA | Secuencial |
| Bug fix + deploy | Dev → QA → DevOps | Secuencial |
| Nuevo proyecto | BMAD → PM → Arch → Dev | Secuencial |
| Issue autónomo | SWE → Dev → QA | Secuencial |
| API con frontend | Dev + Frontend | Paralelo |
| Security review + deploy | Sec → DevOps | Secuencial |
| Mejora de agente | AI + Prompt → QA (Evals) | Semi-paralelo |

### Anti-Patrones de Routing

| ❌ Anti-Patrón | ✅ Corrección |
|---------------|-------------|
| Enviar todo a `/dev` | Clasificar primero, delegar al experto |
| Saltar `/pm` en features nuevas | Siempre definir requisitos antes de implementar |
| Ignorar `/sec` antes de producción | Security review obligatorio para auth/data |
| Usar `/orch` para tareas simples | Solo usar cuando hay ambigüedad real |
| No usar `/bmad` con tareas ambiguas | Clasificar nivel de complejidad primero |
