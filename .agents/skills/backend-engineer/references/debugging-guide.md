# Debugging Guide — Backend Engineer

> Guía sistemática para debugging en aplicaciones backend.

## Metodología: No Adivines, Mide

```
1. REPRODUCIR → 2. AISLAR → 3. ANALIZAR → 4. HIPÓTESIS → 5. VERIFICAR → 6. FIX
```

## Paso 1: Reproducir el Problema

### Crear un Test Case que Falle

```python
# tests/test_reproduce_bug.py
import pytest


class TestBugReproduction:
    """Reproduce el bug reportado de forma determinista."""

    @pytest.mark.asyncio
    async def test_bug_exact_conditions(self, client):
        """Reproduce las condiciones exactas del bug report."""
        # Arrange: setup exacto del escenario
        payload = {
            "email": "test@example.com",
            "name": "Test User",
        }

        # Act: la acción que causa el bug
        response = await client.post("/api/v1/users", json=payload)

        # Assert: verificar que el bug existe
        assert response.status_code == 500  # Este es el bug
```

## Paso 2: Aislar el Componente

### Checklist de Aislamiento

- [ ] ¿Es un problema de la API (endpoint)?
- [ ] ¿Es un problema del servicio (lógica de negocio)?
- [ ] ¿Es un problema del repositorio (acceso a datos)?
- [ ] ¿Es un problema de la base de datos (query/schema)?
- [ ] ¿Es un problema de red (timeout, DNS)?
- [ ] ¿Es un problema de configuración (env vars)?
- [ ] ¿Es un problema de dependencias (versiones)?

### Técnica: Binary Search Debugging

```python
# Si no sabes dónde falla, añade logs temporales en puntos clave:
import logging
logger = logging.getLogger(__name__)

async def problematic_function(data):
    logger.debug("CHECKPOINT 1: Input recibido", extra={"data": data})

    result = await step_one(data)
    logger.debug("CHECKPOINT 2: Step 1 completado", extra={"result": result})

    processed = await step_two(result)
    logger.debug("CHECKPOINT 3: Step 2 completado", extra={"processed": processed})

    # ... continuar hasta encontrar dónde falla
```

## Paso 3: Analizar Logs

### Expresiones Útiles para Buscar

```bash
# Buscar errores en logs
python -c "
import re, sys
for line in open(sys.argv[1]):
    if any(w in line.lower() for w in ['error', 'exception', 'traceback', 'failed']):
        print(line.strip())
" logs/app.log

# Buscar requests lentos (>1s)
python -c "
import json, sys
for line in open(sys.argv[1]):
    try:
        data = json.loads(line)
        if data.get('duration_ms', 0) > 1000:
            print(f'{data[\"method\"]} {data[\"path\"]} - {data[\"duration_ms\"]}ms')
    except: pass
" logs/access.log
```

## Paso 4: Problemas Comunes

### N+1 Queries

```python
# ❌ N+1: 1 query para users + N queries para orders
users = session.exec(select(User)).all()
for user in users:
    orders = session.exec(select(Order).where(Order.user_id == user.id)).all()

# ✅ JOIN: 1 sola query
from sqlmodel import select
statement = (
    select(User, Order)
    .join(Order, isouter=True)
    .where(User.is_active == True)
)
results = session.exec(statement).all()
```

### Memory Leaks

```python
# Detectar memory leaks con tracemalloc
import tracemalloc

tracemalloc.start()

# ... ejecutar código sospechoso ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### Deadlocks en Base de Datos

```sql
-- Ver locks activos en PostgreSQL
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- Matar query bloqueada
-- SELECT pg_terminate_backend(<pid>);
```

### Connection Pool Exhaustion

```python
# Verificar conexiones activas
import asyncpg

async def check_pool_health(pool: asyncpg.Pool):
    """Diagnóstico del pool de conexiones."""
    return {
        "size": pool.get_size(),
        "free_size": pool.get_idle_size(),
        "min_size": pool.get_min_size(),
        "max_size": pool.get_max_size(),
    }
```

## Herramientas de Debugging

| Herramienta | Uso | Comando |
|-------------|-----|---------|
| **pdb** | Breakpoints interactivos | `import pdb; pdb.set_trace()` |
| **tracemalloc** | Memory profiling | `tracemalloc.start()` |
| **cProfile** | CPU profiling | `python -m cProfile -o output.prof app.py` |
| **py-spy** | Sampling profiler (no intrusivo) | `py-spy top --pid <PID>` |
| **EXPLAIN ANALYZE** | Query analysis | `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` |
| **httpx** | Testing de API | `httpx.get("http://localhost:8000/api")` |
