# Scale-Adaptive Intelligence — BMAD Methodology Reference

> Guía detallada del sistema de niveles de BMAD para clasificar y adaptar el esfuerzo de planificación.

## El Problema que Resuelve

No todas las tareas necesitan el mismo nivel de planificación:
- Un hotfix de 1 línea NO necesita un PRD formal
- Un MVP de producto SÍ necesita especificación completa

**BMAD resuelve esto** clasificando la tarea en un nivel (0-4) y adaptando el proceso automáticamente.

## Los 5 Niveles

### Level 0: Quick Fix
```
Esfuerzo: < 5 minutos
Planning: Ninguno
Workflow: Directo
Ejemplo: Fix typo, actualizar variable de entorno, corregir import
```

**Señales:**
- Cambio en 1 archivo
- Sin lógica nueva
- Sin riesgo de regresión

**Acción del Orchestrator:** Delegar directamente a `/dev`

---

### Level 1: Simple Task
```
Esfuerzo: < 2 horas
Planning: Mental (plan breve)
Workflow: Plan → Implement → Test
Ejemplo: Agregar endpoint CRUD, nuevo componente, fix de bug simple
```

**Señales:**
- 1-3 archivos
- Lógica simple y contenida
- Patrones existentes a seguir

**Acción del Orchestrator:** Delegar a persona específica con contexto

---

### Level 2: Feature
```
Esfuerzo: 2 horas - 2 días
Planning: spec.yaml (informal)
Workflow: Specify → Plan → Implement → Verify
Ejemplo: Feature nueva con backend + frontend, integración de API externa
```

**Señales:**
- 3-10 archivos
- Cruza 2+ dominios (backend + frontend)
- Necesita alineación con PM

**Acción del Orchestrator:** Activar `/spec-dev` pipeline

---

### Level 3: Epic
```
Esfuerzo: 3 días - 2 semanas
Planning: spec.yaml + plan.yaml + tasks.yaml (formal)
Workflow: SPEC DRIVEN completo (5 fases)
Ejemplo: Sistema de autenticación, dashboard de analytics, módulo de pagos
```

**Señales:**
- 10+ archivos
- Múltiples personas involucradas
- Decisiones de arquitectura requeridas
- Tests de integración necesarios

**Acción del Orchestrator:** Pipeline SPEC DRIVEN completo con gates

---

### Level 4: Project
```
Esfuerzo: > 2 semanas
Planning: Roadmap + múltiples specs
Workflow: Multi-sprint, múltiples EPICs
Ejemplo: MVP completo, migración de plataforma, rewrite de módulo
```

**Señales:**
- Sistema completo o subsistema mayor
- Múltiples stakeholders
- Riesgos técnicos significativos
- Requiere POC o prototipo

**Acción del Orchestrator:** Descomponer en múltiples Level 3 EPICs

## Tabla de Decisión Rápida

| Pregunta | <5 min | <2h | <2d | <2 sem | >2 sem |
|----------|--------|-----|-----|--------|--------|
| **Level** | 0 | 1 | 2 | 3 | 4 |
| **spec.yaml** | ❌ | ❌ | ✅ informal | ✅ formal | ✅ formal |
| **plan.yaml** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **tasks.yaml** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **ADR** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Code Review** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Tests** | Opcional | ✅ Unit | ✅ + Integr. | ✅ + E2E | ✅ Full |

## Frameworks de Ideación (para kickoff)

### SCAMPER
Para generar ideas a partir de algo existente:
- **S**ubstitute: ¿Qué puedo reemplazar?
- **C**ombine: ¿Qué puedo combinar?
- **A**dapt: ¿Qué puedo adaptar de otro contexto?
- **M**odify: ¿Qué puedo modificar/magnificar/minimizar?
- **P**ut to other use: ¿Para qué más sirve?
- **E**liminate: ¿Qué puedo eliminar?
- **R**everse: ¿Qué pasa si lo invierto?

### 5 Whys
Para encontrar la causa raíz de un problema:
```
Problema: "Los usuarios abandonan el checkout"
Why 1: Porque el formulario es largo
Why 2: Porque pedimos datos innecesarios
Why 3: Porque nadie revisó los campos requeridos
Why 4: Porque no hay un PM asignado al flujo
Why 5: Porque no priorizamos UX del checkout
→ Root Cause: Falta de ownership de UX en flujos críticos
```

### Crazy 8s
Para prototipar rápido:
1. Dividir una hoja en 8 secciones
2. 1 minuto por sección: dibujar una idea
3. Votar las mejores 2
4. Iterar sobre las ganadoras
