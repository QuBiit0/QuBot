# Caching Patterns Reference — Performance Engineer

> Patrones y estrategias de caché para aplicaciones de alto rendimiento.

## Cuando Cachear (y Cuando NO)

### ✅ Cachear Cuando:
- Datos se leen mucho más de lo que se escriben (read-heavy)
- El cálculo/query es costoso (>100ms)
- Los datos pueden tolerar estar "stale" por un periodo
- Múltiples usuarios piden los mismos datos

### ❌ NO Cachear Cuando:
- Datos cambian frecuentemente y la consistencia es crítica
- Cada request es único (alta cardinalidad)
- Los datos son sensibles y no deben persistir
- El costo de invalidación supera el beneficio

## Estrategias de Caché

### 1. Cache-Aside (Lazy Loading)

```
Request → ¿Existe en cache?
            ├── SÍ → Retornar del cache (Cache HIT)
            └── NO → Buscar en DB → Guardar en cache → Retornar (Cache MISS)
```

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

async def get_user(user_id: str) -> dict:
    cache_key = f"user:{user_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss: fetch from DB
    user = await db.get_user(user_id)
    if user:
        redis_client.setex(cache_key, 3600, json.dumps(user))  # TTL: 1 hora

    return user
```

**Pros:** Solo cachea datos que se piden. Simple.
**Cons:** Primer request siempre es lento (cold start).

### 2. Write-Through

```
Escritura → Actualizar DB → Actualizar Cache → Response
```

```python
async def update_user(user_id: str, data: dict) -> dict:
    # Update DB
    user = await db.update_user(user_id, data)

    # Update cache
    cache_key = f"user:{user_id}"
    redis_client.setex(cache_key, 3600, json.dumps(user))

    return user
```

**Pros:** Cache siempre consistente con DB.
**Cons:** Escrituras más lentas (doble write).

### 3. Write-Behind (Write-Back)

```
Escritura → Actualizar Cache → Response
                    ↓ (async)
              Actualizar DB  (batch/scheduled)
```

**Pros:** Escrituras muy rápidas.
**Cons:** Riesgo de pérdida de datos si cache falla.

### 4. Cache Invalidation

```python
# Al modificar un recurso, invalidar su cache
async def delete_user(user_id: str):
    await db.delete_user(user_id)

    # Invalidar cache
    redis_client.delete(f"user:{user_id}")

    # Invalidar caches relacionados
    keys = redis_client.keys(f"user:{user_id}:*")
    if keys:
        redis_client.delete(*keys)

    # Invalidar caches de listas
    redis_client.delete("users:list")
```

## Cache Stampede Protection

Cuando muchos requests llegan al mismo tiempo para un key que expiró:

```python
from redis.lock import Lock

async def get_with_lock(key: str, fetch_func, ttl: int = 3600):
    """Get con protección contra stampede usando lock."""
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Solo un thread/proceso regenera el cache
    lock = Lock(redis_client, f"lock:{key}", timeout=10)

    if lock.acquire(blocking=True, blocking_timeout=5):
        try:
            # Double-check después del lock
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)

            result = await fetch_func()
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        finally:
            lock.release()
    else:
        # Otro proceso está regenerando, esperar y reintentar
        await asyncio.sleep(0.5)
        return await get_with_lock(key, fetch_func, ttl)
```

## TTL Strategy

| Tipo de Dato | TTL Recomendado | Razón |
|-------------|----------------|-------|
| User profile | 1 hora | Cambia poco |
| Product listing | 5-15 min | Cambios moderados |
| Session data | 30 min | Seguridad |
| API response (external) | 5 min | Datos de terceros |
| Static config | 24 horas | Casi nunca cambia |
| Real-time data | 10-30 seg | Está fresco |
| Counters/stats | 1 min | Toleran estar stale |

## HTTP Cache Headers

```python
from fastapi import Response

@app.get("/api/products")
async def get_products(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 min
    response.headers["ETag"] = compute_etag(products)
    return products

@app.get("/api/user/profile")
async def get_profile(response: Response):
    response.headers["Cache-Control"] = "private, max-age=3600"  # 1 hora, no CDN
    return profile

@app.get("/api/sensitive")
async def get_sensitive(response: Response):
    response.headers["Cache-Control"] = "no-store"  # Nunca cachear
    return sensitive_data
```

## Métricas a Monitorear

| Métrica | Target | Acción si Falla |
|---------|--------|-----------------|
| Cache Hit Ratio | > 90% | Aumentar TTL o pre-warm |
| Cache Miss Rate | < 10% | Revisar key strategy |
| Cache Latency (P95) | < 5ms | Verificar Redis health |
| Memory Usage | < 80% | Eviction policy o más memoria |
| Eviction Rate | < 1% | Más memoria o reducir TTL |
