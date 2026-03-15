# Routing de Metodologías

> Guía para que el Orchestrator sepa cuándo y cómo activar las 3 metodologías del framework.

## Las 3 Metodologías

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LMAgent Methodology Stack                            │
│                                                                         │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐    │
│   │     BMAD      │   │   SWE-Agent   │   │   Spec-Driven Dev     │    │
│   │  (/bmad)      │   │    (/swe)     │   │     (/spec-dev)       │    │
│   │               │   │               │   │                       │    │
│   │ Classify &    │   │ Resolve &     │   │ Specify &             │    │
│   │ Orchestrate   │   │ Debug         │   │ Implement             │    │
│   └───────┬───────┘   └───────┬───────┘   └───────────┬───────────┘    │
│           │                   │                       │                │
│           ▼                   ▼                       ▼                │
│   Scale-Adaptive        Trajectory-Based        Pipeline Formal        │
│   Intelligence          Issue Resolution        YAML Artifacts         │
│   (Levels 0-4)          (Edit-Lint-Test)        (spec→plan→tasks)      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Árbol de Decisión

```
¿El usuario tiene una tarea?
│
├── ¿Sabe qué nivel de complejidad es?
│   ├── NO → Activar /bmad (classify)
│   └── SÍ  → Continuar
│
├── ¿Es un GitHub Issue o bug para resolver autónomamente?
│   ├── SÍ → Activar /swe (trajectory-based resolution)
│   └── NO → Continuar
│
├── ¿Es Level 2+ y necesita especificación formal?
│   ├── SÍ → Activar /spec-dev (5-phase pipeline)
│   └── NO → Routing normal a persona específica
│
└── ¿Es un proyecto nuevo desde cero?
    ├── SÍ → /bmad (classify) → /spec-dev (pipeline) → personas por fase
    └── NO → Routing normal
```

## Señales de Activación

### `/bmad` — BMAD Methodology

**Activar cuando el usuario dice:**
- "No sé por dónde empezar"
- "¿Qué tan complejo es esto?"
- "Necesito iniciar un proyecto nuevo"
- "Quiero hacer un brainstorming"
- "Clasifica esta tarea"
- "¿Qué nivel de planning necesita esto?"

**Keywords detectables:**
`clasificar`, `complejidad`, `nivel`, `nuevo proyecto`, `kickoff`, `brainstorm`, `ideación`, `SCAMPER`, `5 Whys`

**Output esperado:**
- Nivel asignado (0-4)
- Recomendación de workflow
- Personas sugeridas

### `/swe` — SWE-Agent

**Activar cuando el usuario dice:**
- "Resolvé este issue"
- "Debugeá este problema paso a paso"
- "Necesito una resolución autónoma"
- "Investigá y arreglá este bug"
- "#123" (referencia a GitHub Issue)

**Keywords detectables:**
`issue`, `bug`, `resolver`, `debugear`, `paso a paso`, `autónomo`, `trajectory`, `reproducir`

**Output esperado:**
- Trajectory log con pasos THINK→ACT→OBSERVE→EVAL
- Fix implementado y testeado
- PR listo para review

### `/spec-dev` — Spec-Driven Agentic Development

**Activar cuando el usuario dice:**
- "Necesito crear una spec para esta feature"
- "Quiero desarrollo guiado por especificación"
- "Necesito trazabilidad completa"
- "Hagamos esto con el pipeline SPEC"

**Keywords detectables:**
`spec`, `especificación`, `plan`, `pipeline`, `trazabilidad`, `feature compleja`, `Level 2`, `Level 3`

**Output esperado:**
- `spec.yaml` → `plan.yaml` → `tasks.yaml`
- Código implementado según spec
- Verificación contra acceptance criteria

## Integración con el Orchestrator

### Flujo Completo de una Tarea

```
1. Usuario envía input
2. Orchestrator clasifica (tipo + dominio + complejidad)
3. Si complejidad desconocida → /bmad classify
4. Si es issue autónomo → /swe resolve
5. Si es Level 2+ → /spec-dev pipeline
6. Si es simple → routing directo a persona
7. Orchestrator monitorea y coordina handoffs
8. Validación final con /qa
```

### Regla de Oro
> **Las metodologías son meta-skills**: no implementan código directamente, sino que **guían el proceso** de las personas que sí lo hacen. El Orchestrator las usa para decidir CÓMO trabajar, no para hacer el trabajo.
