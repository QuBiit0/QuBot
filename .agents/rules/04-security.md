# LMAgent Security Rules

> **Tipo**: `rule` | **Versión**: 3.0.0 | **Actualización**: 2026-02

## 📌 Quick Reference

| Principio | Regla |
|-----------|-------|
| **Secrets** | NUNCA en código. Siempre `os.getenv()` o Vault. |
| **Passwords** | bcrypt/argon2. NUNCA MD5/SHA1. |
| **JWT** | RS256 preferido. Access token = 15 min máx. |
| **SQL** | Queries parametrizadas SIEMPRE. Nunca f-strings. |
| **Inputs** | Validar con Pydantic. Never trust user input. |
| **Headers** | HTTPS + HSTS + CSP obligatorios en prod. |

### 👥 Roles que usan esta regla
`security-analyst`, `backend-engineer`, `devops-engineer`, `architect`

---

Este documento define las reglas y mejores prácticas de seguridad del framework.

> ⚠️ **FLEXIBILIDAD DE LIBRERÍAS**: Las librerías y algoritmos de seguridad expuestos (ej. `passlib`, `slowapi`, RS256) actúan como **ejemplos de referencia**. Tienes total libertad y responsabilidad para evaluar y utilizar los estándares más robustos, seguros y modernos disponibles en el momento de la implementación.

## 🔐 Principios Generales

1. **Defense in Depth**: Múltiples capas de seguridad
2. **Least Privilege**: Mínimos permisos necesarios
3. **Secure by Default**: Configuración segura por defecto
4. **Zero Trust**: No confiar en ningún input

---

## Autenticación

### JWT Best Practices

```python
# ✅ BUENO
JWT_SETTINGS = {
    "algorithm": "RS256",  # Asimétrico
    "access_token_expire": 15,  # minutos
    "refresh_token_expire": 7 * 24 * 60,  # 7 días
}

# ❌ MALO
JWT_SETTINGS = {
    "algorithm": "HS256",  # Simétrico con secret débil
    "access_token_expire": 60 * 24 * 365,  # 1 año
}
```

### Password Storage

```python
# Usar bcrypt o argon2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### MFA

- Implementar TOTP para cuentas sensibles
- Usar librerías probadas (pyotp)
- Backup codes obligatorios

---

## Autorización

### RBAC Pattern

```python
class Permission(Enum):
    READ_USERS = "users:read"
    WRITE_USERS = "users:write"
    DELETE_USERS = "users:delete"
    ADMIN = "*"

class Role:
    ADMIN = [Permission.ADMIN]
    EDITOR = [Permission.READ_USERS, Permission.WRITE_USERS]
    VIEWER = [Permission.READ_USERS]
```

### Middleware de Autorización

```python
def require_permission(permission: Permission):
    async def dependency(user: User = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return Depends(dependency)

@router.delete("/users/{id}")
async def delete_user(
    id: str,
    user: User = require_permission(Permission.DELETE_USERS)
):
    ...
```

---

## Input Validation

### Pydantic Validators

```python
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    
    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

### SQL Injection Prevention

```python
# ✅ BUENO: Parameterized queries
await conn.execute(
    "SELECT * FROM users WHERE email = $1",
    email
)

# ❌ MALO: String interpolation
await conn.execute(
    f"SELECT * FROM users WHERE email = '{email}'"
)
```

### XSS Prevention

```typescript
// ✅ BUENO: React escapa automáticamente
<div>{userInput}</div>

// ❌ MALO: dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// Si necesitas HTML, sanitizar primero
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
```

### 🤖 LLM & Prompt Injection Prevention (OWASP Top 10 para LLMs)
Cuando construyas integraciones con LLMs, **NUNCA** confíes en el input del usuario:
1. **Delimitación Transparente**: Usa delimitadores robustos (`"""`, `xml tags`) para separar las instrucciones del usuario del System Prompt.
2. **Post-Prompting**: Coloca las restricciones más críticas al *final* del prompt, ya que los LLMs prestan más atención (Recency bias) al final.
3. **Sandboxing de Tools**: Si un agente tiene una herramienta de `run_bash_command` o `execute_sql`, la conexión DEBE operar bajo un rol de Read-Only o en un contenedor Docker aislado.

---

## Secrets Management

### Variables de Entorno

```bash
# .env (NUNCA en git)
DATABASE_URL=postgresql://user:pass@localhost/db
JWT_SECRET_KEY=super-secret-key
API_KEY=sk_live_xxxx
```

### Nunca en Código

```python
# ❌ MALO
API_KEY = "sk_live_1234567890"

# ✅ BUENO
API_KEY = os.getenv("API_KEY")
```

### Rotación de Secrets

- Rotar cada 90 días (mínimo)
- Tener proceso de rotación automatizado
- Invalidar secrets comprometidos inmediatamente

---

## Headers de Seguridad

### FastAPI/Starlette

```python
from starlette.middleware.cors import CORSMiddleware
from secure import Secure

secure_headers = Secure()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    secure_headers.framework.headers(response.headers)
    return response
```

### Headers Recomendados

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/search")
@limiter.limit("10/minute")
async def search(request: Request):
    ...
```

---

## Logging de Seguridad

### Qué Logear

```python
# ✅ Logear
logger.info("Login successful", extra={
    "user_id": user.id,
    "ip": request.client.host
})

logger.warning("Login failed", extra={
    "email": email,  # No password
    "ip": request.client.host,
    "reason": "invalid_password"
})

# ❌ NUNCA logear
logger.info(f"Login with password: {password}")  # Contraseñas
logger.info(f"Card number: {card_number}")  # PII
```

---

## Security Checklist

```markdown
## Para cada endpoint
- [ ] Autenticación requerida
- [ ] Autorización verificada
- [ ] Input validado
- [ ] Output sanitizado
- [ ] Rate limiting

## Para deployment
- [ ] HTTPS obligatorio
- [ ] Headers de seguridad
- [ ] Secrets en env vars
- [ ] Logs sin PII
- [ ] Dependency audit

## Periódico
- [ ] Rotar secrets (90 días)
- [ ] Actualizar dependencias
- [ ] Revisar logs de auth
- [ ] Penetration testing (anual)
```

---

## Tools de Seguridad

| Tool | Uso |
|------|-----|
| Bandit | Static analysis Python |
| Safety | Dependency vulnerabilities |
| Snyk | Multi-language security |
| Trivy | Container scanning |
| OWASP ZAP | Dynamic testing |

---

## ✅ Checklist de Seguridad (Antes de Deploy)
- [ ] **Secretos**: Ningún secreto en código/git (`gitleaks detect`)
- [ ] **Auth**: Endpoints protegidos por default (deny-all)
- [ ] **Inputs**: Pydantic models para TO-DO input
- [ ] **Headers**: HTTPS + HSTS + CSP habilitados
- [ ] **SQL**: Cero f-strings en queries
- [ ] **Deps**: `npm audit` / `pip-audit` limpios
- [ ] **Logs**: No PII ni clues en logs
- [ ] **Rate Limit**: Configurado en endpoints públicos (no XSS)

### Auth
- [ ] JWT con expiración corta (<= 15 min)
- [ ] Passwords con bcrypt/argon2
- [ ] RBAC implementado correctamente

### Infra
- [ ] HTTPS obligatorio
- [ ] Headers de seguridad configurados
- [ ] Rate limiting en endpoints públicos
- [ ] Logs sin PII ni passwords
