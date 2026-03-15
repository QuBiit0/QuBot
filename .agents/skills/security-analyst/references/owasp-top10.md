# OWASP Top 10 (2021) + LLM Top 10 — Security Analyst Reference

> Referencia rápida para revisión de seguridad de aplicaciones web y sistemas con IA.

## OWASP Top 10 — Web Applications (2021)

### A01: Broken Access Control

**Riesgo:** Usuarios acceden a recursos que no deberían.

**Verificar:**
- [ ] RBAC implementado (roles y permisos)
- [ ] Validación de ownership en cada endpoint (`user_id == resource.owner_id`)
- [ ] CORS configurado correctamente
- [ ] Tokens de sesión invalidados en logout
- [ ] Rate limiting en endpoints sensibles

```python
# ✅ Patrón correcto: verificar ownership
@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, current_user: User = Depends(get_current_user)):
    order = await order_service.get(order_id)
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return order
```

### A02: Cryptographic Failures

**Riesgo:** Datos sensibles expuestos por cifrado débil o inexistente.

**Verificar:**
- [ ] Passwords hasheados con bcrypt/argon2 (no MD5/SHA1)
- [ ] HTTPS obligatorio en producción
- [ ] Secrets en env vars, nunca en código
- [ ] Datos PII encriptados en reposo
- [ ] TLS 1.2+ en conexiones de DB

### A03: Injection

**Riesgo:** SQL injection, NoSQL injection, OS command injection.

**Verificar:**
- [ ] Queries parametrizadas (ORM o prepared statements)
- [ ] Validación estricta de inputs (Pydantic/Zod)
- [ ] No construir SQL con f-strings
- [ ] Sanitizar inputs para templates (XSS)

```python
# ❌ VULNERABLE: SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ SEGURO: Parametrizado
statement = select(User).where(User.email == email)
```

### A04: Insecure Design

**Verificar:**
- [ ] Threat model documentado
- [ ] Principio de menor privilegio aplicado
- [ ] Business logic validada (no solo inputs)
- [ ] Rate limiting en auth endpoints
- [ ] Timeout en sesiones

### A05: Security Misconfiguration

**Verificar:**
- [ ] Debug mode OFF en producción
- [ ] Headers de seguridad (CSP, HSTS, X-Frame-Options)
- [ ] Stack traces no expuestos al usuario
- [ ] Puertos innecesarios cerrados
- [ ] Default credentials removidas

### A06: Vulnerable Components

**Verificar:**
- [ ] Dependencias actualizadas (`pip audit`, `npm audit`)
- [ ] No usar librerías abandonadas
- [ ] Lock files versionados (`requirements.txt`, `package-lock.json`)

### A07: Auth Failures

**Verificar:**
- [ ] Multi-factor authentication disponible
- [ ] Políticas de password fuertes
- [ ] Brute force protection (rate limiting + lockout)
- [ ] Tokens con expiration corta
- [ ] Refresh tokens con rotación

### A08: Software Integrity

**Verificar:**
- [ ] CI/CD pipeline asegurado
- [ ] Docker images escaneadas
- [ ] Dependencias verificadas (checksums)

### A09: Logging & Monitoring

**Verificar:**
- [ ] Auth events loggeados (login, logout, failed attempts)
- [ ] Errores con suficiente contexto (sin datos sensibles)
- [ ] Alertas configuradas para anomalías
- [ ] Logs protegidos contra tampering

### A10: SSRF (Server-Side Request Forgery)

**Verificar:**
- [ ] URLs externas validadas (whitelist)
- [ ] No permitir requests a IPs internas (127.0.0.1, 10.x, 172.x)
- [ ] Metadata endpoints bloqueados (169.254.169.254)

---

## OWASP Top 10 for LLMs (2025)

### LLM01: Prompt Injection

**Riesgo:** Input malicioso que manipula el comportamiento del LLM.

**Mitigación:**
- [ ] System prompt con instrucciones claras de boundaries
- [ ] Separación de datos de usuario y contexto del sistema
- [ ] Output validation (no ejecutar código generado sin revisión)
- [ ] Sandboxing de tool calls

### LLM02: Insecure Output Handling

**Riesgo:** Output del LLM usado sin sanitizar (XSS, SQL injection vía LLM).

**Mitigación:**
- [ ] Sanitizar todo output del LLM antes de renderizar en UI
- [ ] No usar output del LLM directamente en queries
- [ ] Validar formato de output con schemas

### LLM03: Training Data Poisoning

**Mitigación:**
- [ ] Fuentes de datos verificadas
- [ ] Validación de datos de fine-tuning

### LLM04: Model Denial of Service

**Mitigación:**
- [ ] Límites de tokens por request
- [ ] Rate limiting por usuario
- [ ] Timeouts en llamadas a LLM
- [ ] Cost tracking habilitado

### LLM05: Supply Chain Vulnerabilities

**Mitigación:**
- [ ] Modelos de fuentes confiables
- [ ] Verificar integridad de plugins/tools

### LLM06: Sensitive Information Disclosure

**Mitigación:**
- [ ] No incluir datos sensibles en prompts
- [ ] PII filtering en inputs y outputs
- [ ] Data Loss Prevention (DLP) en pipeline

### LLM07: Insecure Plugin Design

**Mitigación:**
- [ ] Principio de menor privilegio en tools
- [ ] Input validation estricta para tool parameters
- [ ] Confirmación humana para acciones destructivas

### LLM08: Excessive Agency

**Mitigación:**
- [ ] Limitar las tools disponibles al mínimo necesario
- [ ] Human-in-the-loop para acciones irreversibles
- [ ] Logging completo de tool calls (trajectory)

### LLM09: Overreliance

**Mitigación:**
- [ ] Disclaimer visible sobre limitaciones de IA
- [ ] Verificación humana de outputs críticos

### LLM10: Model Theft

**Mitigación:**
- [ ] API keys rotadas regularmente
- [ ] Rate limiting para prevenir model extraction
- [ ] Monitoring de uso anómalo
