# Index Strategy Guide — Data Engineer

> Guía completa para estrategia de índices en PostgreSQL.

## Regla de Oro

> **No crees índices prematuramente.** Crea índices basados en queries reales que observas en producción vía `pg_stat_statements` y `EXPLAIN ANALYZE`.

## Tipos de Índices

| Tipo | Cuándo Usar | Ejemplo |
|------|------------|---------|
| **B-Tree** (default) | Igualdad, rango, ORDER BY | `CREATE INDEX idx_users_email ON users(email)` |
| **Hash** | Solo igualdad, reads pesados | `CREATE INDEX idx_users_uuid ON users USING hash(uuid)` |
| **GIN** | Arrays, JSONB, full-text search | `CREATE INDEX idx_data_tags ON items USING gin(tags)` |
| **GiST** | Geoespacial, rangos, proximidad | `CREATE INDEX idx_locations ON places USING gist(location)` |
| **BRIN** | Datos naturalmente ordenados (timestamps) | `CREATE INDEX idx_logs_created ON logs USING brin(created_at)` |

## Patrones de Índices

### 1. Índice Simple

```sql
-- Para filtros frecuentes en una columna
CREATE INDEX idx_orders_status ON orders(status);
```

### 2. Índice Compuesto

```sql
-- Para queries que filtran por múltiples columnas
-- IMPORTANTE: el orden importa (left-to-right)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Este índice sirve para:
-- ✅ WHERE user_id = X
-- ✅ WHERE user_id = X AND status = Y
-- ❌ WHERE status = Y (no usa el índice)
```

### 3. Índice Parcial

```sql
-- Solo indexa un subconjunto de filas
-- Ideal para queries que siempre filtran lo mismo
CREATE INDEX idx_orders_pending
ON orders(created_at)
WHERE status = 'pending';
-- Mucho más pequeño que indexar toda la tabla
```

### 4. Índice Covering (INCLUDE)

```sql
-- Incluye columnas extra para evitar table lookup
CREATE INDEX idx_orders_user_covering
ON orders(user_id)
INCLUDE (status, total, created_at);
-- Index-Only Scan: no necesita ir a la tabla
```

### 5. Índice Unique

```sql
-- Garantiza unicidad a nivel de DB
CREATE UNIQUE INDEX unq_users_email ON users(email);

-- Unique parcial (solo activos)
CREATE UNIQUE INDEX unq_users_active_email
ON users(email)
WHERE deleted_at IS NULL;
```

### 6. Índice para JSONB

```sql
-- GIN para queries dentro de JSONB
CREATE INDEX idx_items_metadata ON items USING gin(metadata);

-- Soporta:
-- WHERE metadata @> '{"category": "electronics"}'
-- WHERE metadata ? 'key_name'
```

## Cuándo NO Crear Índices

| Situación | Razón |
|-----------|-------|
| Tablas con < 1000 filas | Seq Scan es más rápido |
| Columnas con muy baja cardinalidad (ej: boolean) | El índice no ayuda |
| Tablas con muchos INSERT/UPDATE | Los índices penalizan escrituras |
| Columnas que nunca se filtran | Desperdicio de espacio |

## Diagnóstico con EXPLAIN ANALYZE

```sql
-- Siempre usar EXPLAIN (ANALYZE, BUFFERS) para verificar
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders
WHERE user_id = 'abc-123'
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 10;

-- Lo que buscas:
-- ✅ Index Scan / Index Only Scan
-- ⚠️ Bitmap Heap Scan (aceptable para muchos resultados)
-- ❌ Seq Scan en tabla grande = falta índice
-- ❌ Nested Loop con muchas rows = posible N+1
```

## Mantenimiento de Índices

```sql
-- Crear sin bloquear la tabla (CONCURRENTLY)
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);

-- Reconstruir índice fragmentado
REINDEX INDEX CONCURRENTLY idx_users_email;

-- Ver tamaño de índices
SELECT
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size,
    idx_scan AS scans
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```
