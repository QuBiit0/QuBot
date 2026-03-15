# AI Agent Architecture Patterns — AI Agent Engineer

> Patrones de arquitectura para diseñar agentes de IA efectivos.

## Patrones de Agentes

### 1. ReAct (Reasoning + Acting)

```
Pensamiento → Acción → Observación → Pensamiento → ...

Loop:
  1. THINK: "Necesito buscar el archivo donde se define X"
  2. ACT:   grep_search(query="def X", path="src/")
  3. OBSERVE: "Encontrado en src/utils.py:42"
  4. THINK: "Ahora necesito ver el contexto"
  5. ACT:   view_file(path="src/utils.py", lines="35-55")
  ...
```

**Cuándo usar:** Tareas que requieren razonamiento paso a paso con acceso a herramientas.

### 2. Chain of Thought (CoT)

```
Problema → Paso 1 → Paso 2 → ... → Respuesta

"Vamos a resolver esto paso a paso:
1. Primero, entender el error...
2. Luego, localizar la causa raíz...
3. Finalmente, proponer el fix..."
```

**Cuándo usar:** Razonamiento complejo sin necesidad de herramientas.

### 3. Plan and Execute

```
Input → PLANNER → [Step1, Step2, Step3] → EXECUTOR → Output
                                              ↓
                                    Re-plan si falla
```

**Cuándo usar:** Tareas complejas que se benefician de planificación previa.

### 4. Multi-Agent (Especialización)

```
Orchestrator
    ├── Agent A (Backend)     → Código Python
    ├── Agent B (Frontend)    → Código React
    ├── Agent C (QA)          → Tests
    └── Agent D (DevOps)      → Deployment
```

**Cuándo usar:** Tareas que cruzan múltiples dominios de expertise.

## Tool Design

### Principios de Diseño de Tools

| Principio | Descripción |
|-----------|------------|
| **Atomic** | Cada tool hace UNA cosa bien |
| **Idempotent** | Ejecutar 2 veces = mismo resultado |
| **Observable** | Output claro y parseable |
| **Safe** | Acciones destructivas requieren confirmación |
| **Bounded** | Timeout y límites de output |

### Formato de Tool Definition

```yaml
name: search_files
description: |
  Busca archivos por nombre o patrón glob.
  Retorna lista de rutas que coinciden.
parameters:
  query:
    type: string
    required: true
    description: "Patrón de búsqueda (glob)"
  directory:
    type: string
    required: false
    default: "."
    description: "Directorio base de búsqueda"
  max_results:
    type: integer
    required: false
    default: 50
    description: "Máximo de resultados a retornar"
returns:
  type: array
  items:
    type: object
    properties:
      path: {type: string}
      size: {type: integer}
      modified: {type: string}
```

## Context Management

### Ventana de Contexto

```
┌─────────────────────────────────────────────┐
│ System Prompt (fijo)              ~2K tokens │
│ Agent Persona (fijo)              ~1K tokens │
│ Context/Knowledge (dinámico)      ~4K tokens │
│ Conversation History (sliding)    ~8K tokens │
│ Current Task + Tools (variable)   ~2K tokens │
│ Response Space                    ~4K tokens │
├─────────────────────────────────────────────┤
│ TOTAL                            ~21K tokens │
└─────────────────────────────────────────────┘
```

### Estrategias de Compresión

| Estrategia | Cuándo Usar | Reducción |
|-----------|-------------|-----------|
| **Summarization** | Histórico largo | 70-90% |
| **Relevance filter** | Muchos documentos | 50-80% |
| **Chunking** | Archivos grandes | Variable |
| **Sliding window** | Conversaciones largas | 60-80% |
| **Tool output trim** | Outputs verbosos | 50-70% |

## Métricas de Agentes

| Métrica | Descripción | Target |
|---------|------------|--------|
| **Task Completion Rate** | % de tareas resueltas correctamente | > 80% |
| **Steps to Completion** | Promedio de pasos por tarea | < 15 |
| **Token Efficiency** | Tokens usados vs tarea resuelta | Minimizar |
| **Tool Call Accuracy** | % de tool calls exitosas | > 90% |
| **Hallucination Rate** | % de outputs factuales incorrectos | < 5% |
| **Latency** | Tiempo total de resolución | < 60s (simple) |

## Anti-Patterns

| ❌ Anti-Pattern | ✅ Corrección |
|----------------|---------------|
| Loop infinito en razonamiento | Max steps + fallback |
| Tool call con parámetros inventados | Validación estricta |
| Ignorar output de herramienta | Always process OBSERVE |
| Over-planning sin ejecutar | Plan máx 3 steps ahead |
| Repetir la misma acción | Detect duplicates |
| Context overflow sin notice | Monitor token count |
