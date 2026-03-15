# SWE-Agent Trajectory Format — Reference

> Formato de trajectory logging para resolución autónoma de issues.

## ¿Qué es un Trajectory?

Un **trajectory** es el log completo y auditable de todos los pasos que un agente toma para resolver un issue. Incluye: pensamiento, acciones, observaciones y evaluaciones.

## Formato del Loop

```
THINK → ACT → OBSERVE → EVAL → (repeat or FINISH)
```

### Estructura JSON

```json
{
  "trajectory_id": "traj_20240121_abc123",
  "issue": {
    "id": "#42",
    "title": "Login returns 500 on invalid email format",
    "description": "When submitting an invalid email...",
    "labels": ["bug", "priority:high"]
  },
  "agent": "swe-agent",
  "model": "claude-sonnet-4-20250514",
  "started_at": "2024-01-21T10:30:00Z",
  "completed_at": "2024-01-21T10:35:42Z",
  "total_cost_usd": 0.12,
  "total_tokens": 15430,
  "status": "resolved",
  "steps": [
    {
      "step": 1,
      "phase": "THINK",
      "content": "El error 500 en login con email inválido sugiere falta de validación de input. Necesito encontrar el endpoint de auth y verificar las validaciones.",
      "timestamp": "2024-01-21T10:30:05Z"
    },
    {
      "step": 2,
      "phase": "ACT",
      "tool": "grep_search",
      "input": {"query": "def login", "path": "app/"},
      "timestamp": "2024-01-21T10:30:07Z"
    },
    {
      "step": 3,
      "phase": "OBSERVE",
      "content": "Encontrado app/api/v1/endpoints/auth.py:45 - @app.post('/login')",
      "timestamp": "2024-01-21T10:30:08Z"
    },
    {
      "step": 4,
      "phase": "EVAL",
      "content": "Encontré el endpoint. Ahora necesito ver el schema de validación.",
      "score": 0.3,
      "timestamp": "2024-01-21T10:30:09Z"
    }
  ],
  "resolution": {
    "files_modified": ["app/schemas/auth.py", "tests/test_auth.py"],
    "summary": "Agregada validación EmailStr de Pydantic al schema LoginRequest. Esto causa validación 422 en lugar de error 500.",
    "tests_added": 2,
    "tests_passed": true
  }
}
```

## Fases del Trajectory

| Fase | Descripción | Contenido |
|------|------------|-----------|
| **THINK** | Razonamiento del agente | Hipótesis, plan, análisis |
| **ACT** | Acción ejecutada | Tool call con parámetros |
| **OBSERVE** | Resultado de la acción | Output de la tool |
| **EVAL** | Evaluación del progreso | Score 0-1, next step |
| **FINISH** | Conclusión | Resumen y archivos modificados |

## Edit-Lint-Test Loop

El patrón fundamental del SWE-Agent para cada cambio:

```
1. EDIT    → Modificar el código
2. LINT    → Verificar que no hay errores de sintaxis/estilo
3. TEST    → Ejecutar tests relacionados
4. VERIFY  → ¿Tests pasan? ¿Lint limpio?
   ├── SÍ  → Continuar al siguiente cambio
   └── NO  → Volver a EDIT
```

```python
# Implementación del loop
async def edit_lint_test(file: str, changes: dict) -> bool:
    """Ejecuta el loop Edit-Lint-Test para un cambio."""
    # 1. Edit
    apply_changes(file, changes)

    # 2. Lint
    lint_result = run_lint(file)
    if not lint_result.passed:
        revert_changes(file)
        return False

    # 3. Test
    test_result = run_related_tests(file)
    if not test_result.passed:
        revert_changes(file)
        return False

    return True
```

## Safety Limits

| Límite | Valor | Razón |
|--------|------|-------|
| Max steps por trajectory | 30 | Evitar loops infinitos |
| Max tokens por step | 4096 | Control de costos |
| Max costo total (USD) | $1.00 | Límite de gasto |
| Max tiempo total | 10 min | Timeout |
| Max archivos modificados | 10 | Evitar cambios excesivos |
| Max líneas cambiadas | 500 | Scope control |

## Métricas de Resolución

| Métrica | Target | Descripción |
|---------|--------|-------------|
| Resolution Rate | > 70% | % de issues resueltos exitosamente |
| Avg Steps | < 15 | Pasos promedio para resolver |
| Avg Cost | < $0.50 | Costo promedio por issue |
| False Fix Rate | < 5% | Fixes que introducen regresiones |
| Time to Resolution | < 5 min | Tiempo promedio de resolución |
