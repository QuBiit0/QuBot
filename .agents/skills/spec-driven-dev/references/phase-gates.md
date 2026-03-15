# Spec-Driven Dev: Fase Gates Reference

> Criterios de transición entre las 5 fases del pipeline Spec-Driven.

## Las 5 Fases

```
PHASE 1       PHASE 2       PHASE 3       PHASE 4       PHASE 5
SPECIFY    →  PLAN       →  TASKS      →  IMPLEMENT  →  VERIFY
spec.yaml     plan.yaml     tasks.yaml    CODE          REPORT
  /pm          /arch         /dev          /dev+fe       /qa
```

## Criterios Gate por Fase

### Gate 1: SPECIFY → PLAN

**Artefacto requerido:** `spec.yaml`

**Criterios de paso:**
- [ ] Problema claramente definido
- [ ] User stories con acceptance criteria
- [ ] Métricas de éxito definidas (KPIs)
- [ ] Scope explícito (qué SÍ y qué NO incluye)
- [ ] Stakeholders alineados
- [ ] Priorización hecha (MoSCoW o similar)

**Quién aprueba:** Product Manager (`/pm`)

### Gate 2: PLAN → TASKS

**Artefacto requerido:** `plan.yaml`

**Criterios de paso:**
- [ ] ADR(s) escritos para decisiones técnicas
- [ ] Arquitectura diseñada (C4 containers mínimo)
- [ ] Stack tecnológico definido y justificado
- [ ] Fases de implementación definidas
- [ ] Riesgos técnicos identificados
- [ ] Dependencias externas mapeadas

**Quién aprueba:** Architect (`/arch`)

### Gate 3: TASKS → IMPLEMENT

**Artefacto requerido:** `tasks.yaml`

**Criterios de paso:**
- [ ] Tasks atómicas (≤4h cada una)
- [ ] Dependencias entre tasks definidas
- [ ] Orden de ejecución definido
- [ ] Estimaciones en T-shirt sizes
- [ ] Cada task tiene acceptance criteria

**Quién aprueba:** Tech Lead (`/lead`) o Dev (`/dev`)

### Gate 4: IMPLEMENT → VERIFY

**Artefacto requerido:** Código + Tests

**Criterios de paso:**
- [ ] Código implementado y compilando
- [ ] Tests unitarios escritos (coverage ≥ 80%)
- [ ] Lint limpio (no errores)
- [ ] Environment variables documentadas
- [ ] README/docs actualizados
- [ ] PR listo para review

**Quién aprueba:** Developer (`/dev`)

### Gate 5: VERIFY → DONE

**Artefacto requerido:** Reporte de verificación

**Criterios de paso:**
- [ ] Acceptance criteria del spec.yaml cumplidos
- [ ] Tests E2E pasando
- [ ] Performance dentro de SLOs
- [ ] Security review (si aplica)
- [ ] Documentación completa
- [ ] Deploy exitoso (staging mínimo)

**Quién aprueba:** QA Engineer (`/qa`)

## Context Handoff entre Fases

Cada transición entre fases requiere un **handoff** con el siguiente formato:

```markdown
**Handoff: Phase N → Phase N+1**

📄 Estado: [Qué se completó en esta fase]
📁 Artefactos: [Archivos creados/modificados]
📋 Next: [Acción concreta para la siguiente fase]
✅ Criterio: [Cómo saber que la siguiente fase terminó]
⚠️ Riesgos: [Blockers o riesgos identificados]
```

## Excepciones y Bypass

| Situación | Fase que se puede saltar | Condición |
|-----------|------------------------|-----------|
| Hotfix urgente (P0) | SPECIFY, PLAN | Máximo 50 líneas de cambio |
| Level 0-1 task | SPECIFY, PLAN, TASKS | Cambio trivial y auto-contenido |
| Dependencia externa bloqueante | IMPLEMENT | Esperar con timeout documentado |

> **Regla:** Nunca saltear VERIFY. Todo código debe ser verificado.
