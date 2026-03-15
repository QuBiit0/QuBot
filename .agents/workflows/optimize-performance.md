---
description: Workflow para identificar y resolver cuellos de botella de performance
level: 2-3
personas: [backend-engineer, architect]
---

# Optimize Performance Workflow

Este workflow guía la identificación y resolución de problemas de performance.

## Pre-requisitos

1. Leer [AGENTS.md](../../AGENTS.md)
2. Leer [rules/stack.md](../rules/02-tech-stack.md)
3. Definir métricas objetivo de performance

## Información Requerida

1. **Síntoma**: ¿Qué es lento? (endpoint, query, proceso)
2. **Métricas actuales**: ¿Cuánto tarda actualmente?
3. **Métricas objetivo**: ¿Cuánto debería tardar?
4. **Carga**: ¿Cuántas requests/segundo?
5. **Ambiente**: ¿Dev, staging, producción?
6. **Tendencia**: ¿Siempre fue lento o empeoró?

---

## Paso 1: Medir Estado Actual

### 1.1 Identificar Métricas Base

```python
# Agregar timing a endpoints sospechosos
import time
import structlog

logger = structlog.get_logger()

@router.get("/slow-endpoint")
async def slow_endpoint():
    start = time.perf_counter()
    
    # ... lógica ...
    
    elapsed = time.perf_counter() - start
    logger.info("endpoint_timing", endpoint="/slow-endpoint", elapsed_ms=elapsed*1000)
    
    return result
```

### 1.2 Analizar Logs de Timing

```bash
# Buscar endpoints lentos
grep "endpoint_timing" logs/app.log | \
  jq -r '[.endpoint, .elapsed_ms] | @tsv' | \
  sort -t$'\t' -k2 -nr | head -20
```

### 1.3 Profiling (si es necesario)

```python
# Para Python - usar cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Ejecutar código lento
result = slow_function()

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(20)  # Top 20 funciones lentas
```

---

## Paso 2: Identificar Cuellos de Botella

### Checklist de Causas Comunes

```
┌─────────────────────────────────────────────────────────────┐
│                    CAUSAS DE LENTITUD                       │
├─────────────────────────────────────────────────────────────┤
│ DATABASE                                                    │
│ [ ] N+1 queries                                             │
│ [ ] Queries sin índices                                     │
│ [ ] Queries que retornan demasiados datos                   │
│ [ ] Locks de base de datos                                  │
│ [ ] Conexiones agotadas                                     │
├─────────────────────────────────────────────────────────────┤
│ CODE                                                        │
│ [ ] Loops ineficientes                                      │
│ [ ] Operaciones síncronas bloqueantes                       │
│ [ ] Serialización/deserialización costosa                   │
│ [ ] Regex complejos                                         │
│ [ ] Cálculos repetidos (sin cache)                          │
├─────────────────────────────────────────────────────────────┤
│ NETWORK                                                     │
│ [ ] APIs externas lentas                                    │
│ [ ] Llamadas secuenciales (deberían ser paralelas)          │
│ [ ] Payloads muy grandes                                    │
│ [ ] DNS resolution lenta                                    │
├─────────────────────────────────────────────────────────────┤
│ MEMORY                                                      │
│ [ ] Memory leaks                                            │
│ [ ] Objetos muy grandes en memoria                          │
│ [ ] Garbage collection frecuente                            │
├─────────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE                                              │
│ [ ] CPU insuficiente                                        │
│ [ ] RAM insuficiente                                        │
│ [ ] Disco I/O lento                                         │
│ [ ] Contenedor con límites muy bajos                        │
└─────────────────────────────────────────────────────────────┘
```

### Análisis de Queries SQL

```python
# Agregar logging de queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# En producción, usar query explain
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

---

## Paso 3: Priorizar Optimizaciones

### Matriz de Priorización

| Optimización | Impacto | Esfuerzo | Riesgo | Prioridad |
|--------------|---------|----------|--------|-----------|
| [Opt 1] | Alto/Medio/Bajo | Alto/Medio/Bajo | Alto/Medio/Bajo | 1-5 |
| [Opt 2] | ... | ... | ... | ... |

**Regla**: Priorizar **Alto Impacto + Bajo Esfuerzo + Bajo Riesgo**

---

## Paso 4: Implementar Optimizaciones

### 4.1 Optimizaciones de Database

#### Agregar Índices
```sql
-- Identificar queries sin índices
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;

-- Crear índice
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Verificar mejora
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;
```

#### Eliminar N+1 Queries
```python
# Antes (N+1)
users = await db.query(User).all()
for user in users:
    orders = await db.query(Order).filter(Order.user_id == user.id).all()

# Después (JOIN o eager loading)
users = await db.query(User).options(selectinload(User.orders)).all()
```

#### Paginar Resultados
```python
# Antes
all_orders = await repository.get_all()  # Puede ser millones

# Después
orders = await repository.get_paginated(page=1, page_size=100)
```

### 4.2 Optimizaciones de Código

#### Agregar Cache
```python
from functools import lru_cache
import redis

redis_client = redis.Redis.from_url(settings.REDIS_URL)

async def get_user_settings(user_id: int) -> dict:
    """Obtiene settings con cache en Redis."""
    cache_key = f"user_settings:{user_id}"
    
    # Intentar cache primero
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Si no hay cache, obtener de DB
    settings = await repository.get_settings(user_id)
    
    # Guardar en cache (5 minutos)
    await redis_client.setex(cache_key, 300, json.dumps(settings))
    
    return settings
```

#### Paralelizar Llamadas
```python
import asyncio

# Antes (secuencial) - 3 segundos
user = await get_user(user_id)
orders = await get_orders(user_id)
preferences = await get_preferences(user_id)

# Después (paralelo) - 1 segundo
user, orders, preferences = await asyncio.gather(
    get_user(user_id),
    get_orders(user_id),
    get_preferences(user_id)
)
```

#### Código Async Correcto
```python
# Antes (blocking)
import requests
response = requests.get(url)  # Bloquea event loop!

# Después (async)
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### 4.3 Optimizaciones de Infraestructura

#### Aumentar Pool de Conexiones
```python
# config.py
DATABASE_URL = "postgresql+asyncpg://..."
DATABASE_POOL_SIZE = 20  # Aumentar si hay muchas conexiones
DATABASE_MAX_OVERFLOW = 10
```

#### Agregar Redis para Cache de Sesión
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

## Paso 5: Medir Mejora

### 5.1 Benchmark Antes/Después

```python
# benchmark.py
import asyncio
import time
import httpx
import statistics

async def benchmark_endpoint(url: str, n: int = 100) -> dict:
    """Ejecuta N requests y reporta métricas."""
    times = []
    
    async with httpx.AsyncClient() as client:
        for _ in range(n):
            start = time.perf_counter()
            await client.get(url)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
    
    return {
        "requests": n,
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(n * 0.95)],
        "p99_ms": sorted(times)[int(n * 0.99)]
    }

# Ejecutar
results = asyncio.run(benchmark_endpoint("http://localhost:8000/endpoint"))
print(results)
```

### 5.2 Comparar Resultados

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Avg (ms) | 500 | 50 | 10x |
| P95 (ms) | 800 | 100 | 8x |
| P99 (ms) | 1200 | 150 | 8x |

---

## Paso 6: Documentar

### 6.1 Documentar Optimizaciones

```markdown
# Optimización: [Nombre]

## Problema
- Endpoint: /api/v1/users
- Tiempo promedio: 500ms
- Causa: N+1 queries

## Solución
- Agregar eager loading para orders
- Agregar índice en orders.user_id

## Resultados
- Tiempo promedio: 50ms (10x mejora)
- CPU: -30%
- DB connections: -50%

## Archivos Modificados
- `app/repositories/user_repository.py`
- `migrations/xxx_add_index.sql`
```

### 6.2 Agregar Monitoring Permanente

```python
# Agregar métricas para monitoreo continuo
from prometheus_client import Histogram

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

@router.get("/endpoint")
async def endpoint():
    with REQUEST_LATENCY.labels(endpoint="/endpoint").time():
        return await process()
```

---

## Checklist Final

### Análisis
- [ ] Métricas base medidas
- [ ] Cuellos de botella identificados
- [ ] Causas raíz documentadas

### Implementación
- [ ] Optimizaciones priorizadas
- [ ] Cambios implementados
- [ ] Tests no afectados

### Validación
- [ ] Benchmarks ejecutados
- [ ] Mejora confirmada
- [ ] Sin regresiones

### Documentación
- [ ] Optimizaciones documentadas
- [ ] Monitoring configurado
- [ ] Lecciones aprendidas registradas
