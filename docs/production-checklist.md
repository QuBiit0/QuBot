# Production Deployment Checklist

Use this checklist before every production deployment.

---

## Security

- [ ] `SECRET_KEY` is unique, at least 32 characters, and not committed to source control
- [ ] SSL certificate is valid and auto-renewal is configured
- [ ] CORS `ALLOWED_ORIGINS` is restricted to production domains only (not `*`)
- [ ] Rate limiting is active on auth endpoints (`5/min` login, `3/min` register)
- [ ] Security headers middleware is enabled (`X-Content-Type-Options`, `X-Frame-Options`, `HSTS`)
- [ ] All LLM API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) are valid and have usage limits set
- [ ] `DEBUG=false` in production environment

## Infrastructure

- [ ] PostgreSQL is running and accessible; connection pool settings are configured
- [ ] Redis is running and accessible (required for WebSocket pub/sub and task queue)
- [ ] All Docker containers are healthy (`docker compose ps`)
- [ ] Nginx reverse proxy is configured with SSL and gzip compression
- [ ] Log aggregation is collecting API and worker logs
- [ ] Backups are scheduled and tested (`scripts/backup-db.sh`)

## Application

- [ ] Database migrations are up to date (`alembic upgrade head`)
- [ ] `NEXT_PUBLIC_API_URL` points to the correct backend URL
- [ ] `NEXT_PUBLIC_WS_URL` points to the correct WebSocket URL
- [ ] At least one LLM config is seeded in the database
- [ ] Worker process is running (`python -m app.worker`)

## Monitoring

- [ ] Health check endpoints respond: `GET /api/v1/health` → 200
- [ ] Grafana dashboards are accessible and data is flowing
- [ ] Alerts are configured: error rate > 5%, latency P99 > 2s, worker queue > 100
- [ ] OpenAPI docs are disabled in production

## Code Quality

- [ ] `ruff check .` passes with 0 errors (backend)
- [ ] `tsc --noEmit` passes with 0 type errors (frontend)
- [ ] `pytest --cov=app --cov-fail-under=80` passes
- [ ] `npm run build` succeeds without errors

## Post-Deployment Smoke Tests

- [ ] Login → dashboard loads → agents visible → tasks visible
- [ ] WebSocket connection established (browser DevTools → Network → WS)
- [ ] Chat sends a message and receives a streaming response
- [ ] Kanban drag-and-drop updates task status via API
