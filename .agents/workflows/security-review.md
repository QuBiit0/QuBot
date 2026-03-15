---
description: Workflow para ejecutar una revisión de seguridad
level: 2-3
personas: [security-analyst, backend-engineer]
---

# Security Review Workflow

Este workflow guía una revisión de seguridad de código o cambios.

## Pre-requisitos

1. Leer [AGENTS.md](../../AGENTS.md)
2. Leer [rules/stack.md](../rules/02-tech-stack.md)
3. Leer [personas/security-analyst.md](../skills/security-analyst/SKILL.md)

## Información Requerida

1. **Alcance**: ¿Qué se está revisando? (PR, módulo, sistema completo)
2. **Tipo de cambio**: ¿Nuevo código, refactor, integración?
3. **Datos sensibles**: ¿Se manejan datos PII, financieros, etc.?
4. **Exposición**: ¿Es interno, público, API?

---

## Paso 1: Clasificar Riesgo

### Matriz de Riesgo

| Factor | Bajo | Medio | Alto | Crítico |
|--------|------|-------|------|---------|
| Datos | Públicos | Internos | PII | Financieros/Salud |
| Acceso | Interno | Autenticado | Público | Sin restricción |
| Impacto | UX | Funcional | Datos | Sistema completo |

### Determinar Profundidad de Review

```
Riesgo Bajo    → Quick review (30 min)
Riesgo Medio   → Standard review (1-2 hrs)
Riesgo Alto    → Deep review (4+ hrs)
Riesgo Crítico → Full audit + penetration test
```

---

## Paso 2: Checklist de Seguridad

### Autenticación
- [ ] ¿Se valida el token/sesión en cada request?
- [ ] ¿Los tokens tienen expiración?
- [ ] ¿Se usa HTTPS obligatorio?
- [ ] ¿Hay protección contra brute force?
- [ ] ¿Las contraseñas se hashean correctamente? (bcrypt, argon2)

### Autorización
- [ ] ¿Cada endpoint verifica permisos?
- [ ] ¿Se aplica principio de menor privilegio?
- [ ] ¿Hay separación de roles?
- [ ] ¿Se valida acceso a recursos por owner?

### Input Validation
- [ ] ¿Todos los inputs se validan?
- [ ] ¿Se usa Pydantic/class-validator?
- [ ] ¿Se sanitizan inputs de texto?
- [ ] ¿Hay límites de tamaño?
- [ ] ¿Se rechaza content-type inesperado?

### SQL Injection
- [ ] ¿Se usan queries parametrizadas?
- [ ] ¿No hay concatenación de strings en SQL?
- [ ] ¿Se usa ORM correctamente?

### XSS/Injection
- [ ] ¿Se escapan outputs en HTML?
- [ ] ¿Se usa CSP headers?
- [ ] ¿No hay eval() o exec() con user input?

### Secrets
- [ ] ¿No hay credenciales en código?
- [ ] ¿Se usan variables de entorno?
- [ ] ¿Los secrets no aparecen en logs?
- [ ] ¿.env está en .gitignore?

### Logging
- [ ] ¿Se loguean eventos de seguridad?
- [ ] ¿No se loguean datos sensibles?
- [ ] ¿Hay audit trail para acciones críticas?

### Headers de Seguridad
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] X-XSS-Protection: 1; mode=block
- [ ] Strict-Transport-Security
- [ ] Content-Security-Policy

### Rate Limiting
- [ ] ¿Hay límite de requests?
- [ ] ¿Se limitan operaciones costosas?
- [ ] ¿Hay protección contra DDoS?

### Dependencias
- [ ] ¿Dependencias actualizadas?
- [ ] ¿No hay vulnerabilidades conocidas?
- [ ] ¿Se usa lockfile?

---

## Paso 3: Herramientas de Análisis

### Análisis Estático

```bash
# Python - Bandit
pip install bandit
bandit -r app/

# Python - Safety (dependencias)
pip install safety
safety check

# Node - npm audit
npm audit

# Docker - Trivy
trivy image myapp:latest
```

### Búsqueda de Patrones

```bash
# Buscar secrets hardcodeados
grep -rn "password\s*=" --include="*.py" .
grep -rn "api_key\s*=" --include="*.py" .
grep -rn "secret" --include="*.py" .

# Buscar SQL inseguro
grep -rn "execute(" --include="*.py" .
grep -rn "f\"SELECT" --include="*.py" .

# Buscar eval/exec
grep -rn "eval(" --include="*.py" .
grep -rn "exec(" --include="*.py" .
```

---

## Paso 4: Documentar Findings

### Template de Finding

```markdown
## [SEV-{severity}] {Título del finding}

### Descripción
{Qué es el problema}

### Ubicación
- Archivo: `path/to/file.py`
- Línea: {línea}
- Código:
```python
{código vulnerable}
```

### Impacto
{Qué podría pasar si se explota}

### CVSS Score (opcional)
{Calcular score si aplica}

### Recomendación
{Cómo arreglarlo}

### Código Corregido
```python
{código seguro}
```

### Referencias
- [OWASP Reference](link)
- [CWE Reference](link)
```

### Severidades

| Severidad | Descripción | Acción |
|-----------|-------------|--------|
| CRITICAL | Explotable remotamente, impacto total | Fix inmediato, bloquear merge |
| HIGH | Explotable, impacto significativo | Fix antes de deploy |
| MEDIUM | Requiere condiciones, impacto parcial | Fix en próximo sprint |
| LOW | Difícil explotar, impacto menor | Backlog |
| INFO | Mejora recomendada | Considerar |

---

## Paso 5: Crear Reporte

### Template de Reporte

```markdown
# Security Review Report

## Información General

| Campo | Valor |
|-------|-------|
| Fecha | {fecha} |
| Revisor | {nombre} |
| Alcance | {qué se revisó} |
| Riesgo General | {Bajo/Medio/Alto/Crítico} |

## Resumen Ejecutivo

{1-2 párrafos resumiendo estado general}

## Estadísticas

| Severidad | Cantidad |
|-----------|----------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| Info | {n} |

## Findings

### Critical & High Priority

{Listar findings críticos y altos}

### Medium Priority

{Listar findings medios}

### Low Priority & Info

{Listar o resumir}

## Recomendaciones

1. {Recomendación 1}
2. {Recomendación 2}
3. {Recomendación 3}

## Próximos Pasos

- [ ] Fix critical findings
- [ ] Fix high findings
- [ ] Schedule follow-up review

## Aprobación

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Security Analyst | | | |
| Tech Lead | | | |
```

---

## Paso 6: Seguimiento

### Tracking de Remediation

- [ ] Crear issues para cada finding
- [ ] Asignar prioridades
- [ ] Programar re-review
- [ ] Verificar fixes aplicados
- [ ] Actualizar documentación

### Re-review

Después de fixes:
- [ ] Verificar que cada finding está resuelto
- [ ] No se introdujeron nuevos issues
- [ ] Tests de seguridad pasan
- [ ] Aprobar para merge/deploy

---

## Checklist Final

- [ ] Todos los findings documentados
- [ ] Severidades asignadas
- [ ] Recomendaciones claras
- [ ] Reporte generado
- [ ] Issues creados para tracking
- [ ] Stakeholders notificados
- [ ] Re-review programado
