# Orchestrator Routing Logic

> Documento de referencia detallado para la lógica de routing del Orchestrator.

## Algoritmo de Routing

El Orchestrator sigue un algoritmo de 4 pasos para decidir a quién delegar:

```
INPUT → CLASSIFY → ROUTE → DELEGATE → MONITOR
```

### Paso 1: Clasificar el Input

| Señal | Cómo detectarla | Ejemplo |
|-------|-----------------|---------|
| **Idea vaga** | Sin detalles técnicos, verbos como "quiero", "necesito" | "Quiero una app para gestionar tareas" |
| **Feature request** | Detalles funcionales específicos | "Agrega un endpoint PUT /users/{id}" |
| **Bug report** | Palabras: "falla", "error", "no funciona", stack traces | "El login devuelve 500 cuando..." |
| **Pregunta técnica** | Palabras: "cómo", "por qué", "qué es" | "¿Cómo configuro Redis?" |
| **Tarea operacional** | Palabras: "deploy", "producción", "backup", "Docker" | "Sube esto a staging" |
| **Auditoría** | Palabras: "seguridad", "vulnerabilidad", "revisar" | "Audita este módulo" |
| **Mejora de agente** | Palabras: "prompt", "bot", "alucina", "agente" | "Mejora cómo habla el bot" |
| **Tarea de datos** | Palabras: "query", "migración", "schema", "SQL" | "Optimiza esta query" |
| **Resolución de issue** | Referencias a GitHub Issues, "#123" | "Resolvé el issue #42" |
| **Arranque de proyecto** | Dump de información, "nuevo proyecto" | "Quiero crear un SaaS de..." |

### Paso 2: Detectar el Dominio

| Dominio | Keywords | Persona(s) Principales |
|---------|----------|----------------------|
| Backend | API, endpoint, servidor, FastAPI, NestJS | `/dev` |
| Frontend | React, UI, componente, CSS, Next.js | `/frontend` |
| Base de datos | SQL, schema, migración, query, PostgreSQL | `/dba` |
| Infraestructura | Docker, CI/CD, deploy, Kubernetes | `/devops` |
| Seguridad | Auth, JWT, XSS, inyección, permisos | `/sec` |
| IA/Agentes | Prompt, agente, LLM, tool calling | `/ai` |
| Automatización | n8n, webhook, cron, ETL | `/auto` |
| Producto | PRD, user stories, roadmap, priorización | `/pm` |
| Testing | Tests, coverage, E2E, pytest, jest | `/qa` |
| Performance | Lento, P95, cache, profiling, load test | `/perf` |
| Mobile | React Native, Expo, iOS, Android | `/mobile` |
| Diseño | UI, UX, wireframe, colores, accesibilidad | `/ux` |

### Paso 3: Determinar Complejidad (BMAD Levels)

| Indicador | Level Estimado | Acción |
|-----------|---------------|--------|
| Tarea de menos de 5 min | Level 0 | Delegar directamente |
| Tarea simple, un solo dominio | Level 1 | Delegar con breve plan |
| Tarea que cruza 2+ dominios | Level 2 | Usar workflow `/spec` |
| Feature complejo, múltiples personas | Level 3 | Pipeline SPEC DRIVEN completo |
| Proyecto de empresa, muchos stakeholders | Level 4 | Múltiples aprobaciones, arquitectura formal |

### Paso 4: Construir la Secuencia

**Reglas de secuenciación:**

1. **PM siempre primero** si hay ambigüedad en requisitos
2. **Architect antes de Dev** si hay decisiones de diseño
3. **Security review** antes de deploy a producción
4. **QA siempre al final** para validación
5. **BMAD al inicio** si no está claro el nivel de complejidad

## Routing por Tipo de Metodología

### Cuándo activar `/bmad`
- El usuario no sabe por dónde empezar
- Se necesita clasificar la complejidad de una tarea
- Proyecto nuevo que requiere Scale-Adaptive Intelligence
- Sesión de ideación o brainstorming

### Cuándo activar `/swe`
- GitHub Issue que resolver
- Bug complejo que requiere debugging sistemático
- Tarea que necesita trajectory logging (auditoría)
- Resolución autónoma paso a paso

### Cuándo activar `/spec-dev`
- Feature Level 2+ que necesita especificación formal
- Refactor arquitectural grande
- MVP de producto nuevo
- Cualquier trabajo que requiera trazabilidad spec → code

## Patrones de Routing Multi-Persona

### Patrón: Proyecto Nuevo (Full Stack)
```
/bmad (classify) → /pm (spec) → /arch (plan) → /dev (implement) → /qa (verify)
```

### Patrón: Bug Crítico en Producción
```
/dev (reproduce) → /qa (test case) → /dev (fix) → /sec (review) → /devops (deploy)
```

### Patrón: Feature con Spec Driven
```
/spec-dev (pipeline) → /pm (spec.yaml) → /arch (plan.yaml) → /dev (tasks.yaml + code) → /qa (verify)
```

### Patrón: Resolución Autónoma de Issue
```
/swe (trajectory) → /dev (fix) → /qa (test) → /devops (PR)
```

### Patrón: Mejora de Agente IA
```
/ai (architecture) → /prompt (system prompt) → /qa (evals) → /sec (prompt injection review)
```
