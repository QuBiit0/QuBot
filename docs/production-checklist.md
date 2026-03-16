# Production Deployment Checklist

## Security

- [ ] `SECRET_KEY` is unique, >= 32 chars, stored in a secrets manager (not in `.env` committed to git)
- [ ] `DEBUG=false`
- [ ] `ALLOWED_ORIGINS` restricted to your production domains only
- [ ] SSL certificate configured in nginx (uncomment HTTPS block in `nginx/nginx.conf`)
- [ ] HTTP → HTTPS redirect enabled
- [ ] Rate limiting active (`RATE_LIMIT_ENABLED=true`)
- [ ] All LLM API keys are valid and scoped to minimal permissions
- [ ] `ADMIN_PASSWORD` is strong and changed from the default
- [ ] OpenAPI docs disabled or password-protected (`/docs` and `/redoc`)
- [ ] No hardcoded credentials in any source file (`grep -r "password\|secret\|api_key" --include="*.py" app/`)

## Infrastructure

- [ ] PostgreSQL running with persistent volume
- [ ] Redis running with persistent volume
- [ ] Backups scheduled (`scripts/backup-db.sh` via cron)
- [ ] All Docker healthchecks passing (`docker compose ps`)
- [ ] Nginx proxy config validated (`nginx -t`)
- [ ] Firewall rules: only ports 80/443 publicly exposed

## Application

- [ ] Database migrations applied (`alembic upgrade head` or equivalent)
- [ ] Admin user seeded
- [ ] `NEXT_PUBLIC_API_URL` points to production API
- [ ] `NEXT_PUBLIC_WS_URL` points to production WebSocket
- [ ] Frontend build succeeds (`npm run build`)
- [ ] All environment variables in `.env` are set (compare with `.env.example`)

## Observability

- [ ] Structured logging outputting JSON (check `LOG_LEVEL` and `DEBUG=false`)
- [ ] Log aggregation running (Loki/Promtail or equivalent)
- [ ] Grafana dashboards accessible
- [ ] Health endpoints responding:
  - `GET /health` → nginx
  - `GET /api/v1/health` → backend
- [ ] Alerts configured for: error rate > 5%, P99 latency > 2s, worker queue depth

## Performance

- [ ] Database connection pool sized appropriately (`POOL_SIZE`, `POOL_MAX_OVERFLOW`)
- [ ] Redis memory limits set
- [ ] Nginx gzip compression enabled (already on)
- [ ] Static file caching headers set (already on)
- [ ] Worker replicas >= 2 (`WORKER_REPLICAS=2`)

## CI/CD

- [ ] GitHub Actions CI pipeline passing (`ci.yml`)
- [ ] Branch protection on `main` (require PR + CI pass)
- [ ] Container registry credentials configured
- [ ] Deploy pipeline tested end-to-end

## Post-Deploy Verification

- [ ] Login / register works
- [ ] Agent CRUD works
- [ ] Task CRUD and Kanban drag-drop works
- [ ] WebSocket connection established (check connection indicator in UI)
- [ ] LLM execution works (create agent, run task)
- [ ] Worker processes tasks from queue
- [ ] Logs appearing in aggregator
