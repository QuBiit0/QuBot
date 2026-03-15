-- LMAgent - Queries de Monitoreo PostgreSQL
-- Queries reutilizables para diagnóstico y monitoreo de PostgreSQL.
-- Copiar y pegar según necesidad.

-- ============================================================
-- 1. PERFORMANCE: Queries más lentos
-- ============================================================

-- Top 10 queries más lentos (requiere pg_stat_statements)
SELECT
    query,
    calls,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    round(total_exec_time::numeric, 2) AS total_ms,
    rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- ============================================================
-- 2. PERFORMANCE: Tablas sin índices usados (candidatas a índice)
-- ============================================================

SELECT
    relname AS table_name,
    seq_scan,
    idx_scan,
    CASE WHEN seq_scan > 0
         THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 2)
         ELSE 100
    END AS idx_usage_percent,
    n_live_tup AS estimated_rows
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
  AND n_live_tup > 1000
ORDER BY seq_scan DESC;

-- ============================================================
-- 3. PERFORMANCE: Índices no usados (candidatos a eliminar)
-- ============================================================

SELECT
    schemaname || '.' || relname AS table,
    indexrelname AS index,
    idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================
-- 4. HEALTH: Cache Hit Ratio (debe ser >99%)
-- ============================================================

SELECT
    'index' AS type,
    sum(idx_blks_hit) AS hits,
    sum(idx_blks_read) AS reads,
    round(
        sum(idx_blks_hit)::numeric /
        nullif(sum(idx_blks_hit) + sum(idx_blks_read), 0) * 100, 2
    ) AS hit_ratio
FROM pg_statio_user_indexes
UNION ALL
SELECT
    'table' AS type,
    sum(heap_blks_hit),
    sum(heap_blks_read),
    round(
        sum(heap_blks_hit)::numeric /
        nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2
    )
FROM pg_statio_user_tables;

-- ============================================================
-- 5. HEALTH: Tamaño de tablas
-- ============================================================

SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS data_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- ============================================================
-- 6. HEALTH: Conexiones activas
-- ============================================================

SELECT
    datname AS database,
    usename AS user,
    state,
    count(*) AS connections,
    max(now() - query_start) AS longest_query
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname, usename, state
ORDER BY connections DESC;

-- ============================================================
-- 7. LOCKS: Queries bloqueadas
-- ============================================================

SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS blocked_duration
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid
JOIN pg_locks blk ON blk.locktype = bl.locktype
    AND blk.database IS NOT DISTINCT FROM bl.database
    AND blk.relation IS NOT DISTINCT FROM bl.relation
    AND blk.page IS NOT DISTINCT FROM bl.page
    AND blk.tuple IS NOT DISTINCT FROM bl.tuple
    AND blk.pid != bl.pid
JOIN pg_stat_activity blocking ON blk.pid = blocking.pid
WHERE NOT bl.granted;

-- ============================================================
-- 8. MAINTENANCE: Tablas que necesitan VACUUM
-- ============================================================

SELECT
    relname AS table_name,
    n_dead_tup AS dead_rows,
    n_live_tup AS live_rows,
    round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- ============================================================
-- 9. MIGRATION TEMPLATE
-- ============================================================

-- Up Migration
-- BEGIN;
-- ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);
-- COMMIT;

-- Down Migration (Rollback)
-- BEGIN;
-- DROP INDEX IF EXISTS idx_users_phone;
-- ALTER TABLE users DROP COLUMN IF EXISTS phone;
-- COMMIT;
