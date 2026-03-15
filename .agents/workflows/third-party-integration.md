---
description: Workflow para integración con APIs de terceros
level: 2
personas: [backend-engineer, architect]
---

# Third-Party Integration Workflow

Este workflow guía la integración segura con APIs de terceros.

## Pre-requisitos

1. Documentación de la API externa
2. Credenciales de prueba
3. Límites de rate conocidos

---

## Fase 1: Análisis

### 1.1 Evaluar la API

| Aspecto | Verificar |
|---------|-----------|
| Autenticación | API Key, OAuth, Bearer? |
| Rate Limits | Requests por minuto/hora |
| Formato | REST, GraphQL, SOAP |
| Versioning | ¿La versión es estable? |
| SLA | ¿Garantías de uptime? |

### 1.2 Mapear Endpoints Necesarios

```markdown
| Endpoint | Método | Uso en nuestro sistema |
|----------|--------|------------------------|
| /users   | GET    | Sync usuarios          |
| /orders  | POST   | Crear pedidos          |
```

### 1.3 Diseñar Abstracción

```python
# Interfaz abstracta para evitar vendor lock-in
class PaymentProvider(Protocol):
    async def create_payment(self, amount: Decimal) -> PaymentResult:
        ...
    
    async def get_payment(self, payment_id: str) -> Payment:
        ...
```

---

## Fase 2: Implementación

### 2.1 Configuración

```python
# config/settings.py
class ThirdPartySettings(BaseSettings):
    api_key: str
    api_url: str = "https://api.example.com/v1"
    timeout: int = 30
    max_retries: int = 3
    
    class Config:
        env_prefix = "THIRD_PARTY_"
```

```bash
# .env
THIRD_PARTY_API_KEY=sk_test_xxxx
```

### 2.2 Cliente HTTP

```python
# clients/third_party_client.py
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

class ThirdPartyClient:
    def __init__(self, settings: ThirdPartySettings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.api_url,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            timeout=settings.timeout,
        )
    
    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3)
    )
    async def request(self, method: str, path: str, **kwargs):
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def get_user(self, user_id: str):
        return await self.request("GET", f"/users/{user_id}")
```

### 2.3 Error Handling

```python
# exceptions/third_party.py
class ThirdPartyError(Exception):
    """Base error for third party integration"""

class ThirdPartyRateLimitError(ThirdPartyError):
    """Rate limit exceeded"""
    
class ThirdPartyAuthError(ThirdPartyError):
    """Authentication failed"""

# En el cliente
async def request(self, method: str, path: str, **kwargs):
    try:
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise ThirdPartyRateLimitError("Rate limit exceeded")
        elif e.response.status_code == 401:
            raise ThirdPartyAuthError("Invalid API key")
        raise ThirdPartyError(f"API error: {e}")
```

### 2.4 Caching

```python
# services/cached_third_party.py
from functools import lru_cache
import redis

redis_client = redis.Redis()

async def get_user_cached(user_id: str) -> dict:
    cache_key = f"third_party:user:{user_id}"
    
    # Check cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    user = await client.get_user(user_id)
    
    # Cache for 1 hour
    await redis_client.setex(cache_key, 3600, json.dumps(user))
    
    return user
```

---

## Fase 3: Testing

### 3.1 Mocking

```python
# tests/conftest.py
import respx

@pytest.fixture
def mock_third_party():
    with respx.mock:
        respx.get("https://api.example.com/v1/users/123").mock(
            return_value=httpx.Response(200, json={"id": "123", "name": "Test"})
        )
        yield
```

### 3.2 Test Unitarios

```python
# tests/test_third_party_client.py
async def test_get_user(mock_third_party):
    client = ThirdPartyClient(settings)
    user = await client.get_user("123")
    assert user["id"] == "123"

async def test_rate_limit_handling(mock_third_party):
    respx.get("https://api.example.com/v1/users/123").mock(
        return_value=httpx.Response(429)
    )
    
    with pytest.raises(ThirdPartyRateLimitError):
        await client.get_user("123")
```

### 3.3 Integration Tests

```python
# tests/integration/test_third_party_real.py
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("THIRD_PARTY_API_KEY"), reason="No API key")
async def test_real_api_connection():
    """Test with real API (use sparingly)"""
    client = ThirdPartyClient(settings)
    # Use a safe, idempotent endpoint
    result = await client.health_check()
    assert result["status"] == "ok"
```

---

## Fase 4: Monitoring

### 4.1 Métricas

```python
from prometheus_client import Counter, Histogram

third_party_requests = Counter(
    'third_party_requests_total',
    'Total requests to third party API',
    ['method', 'endpoint', 'status']
)

third_party_latency = Histogram(
    'third_party_request_duration_seconds',
    'Request duration to third party API'
)
```

### 4.2 Alertas

```yaml
# Prometheus alert rules
groups:
  - name: third_party
    rules:
      - alert: ThirdPartyHighErrorRate
        expr: |
          rate(third_party_requests_total{status=~"5.."}[5m]) 
          / rate(third_party_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate with third party API"
```

---

## Checklist

```markdown
## Integration: {nombre}

### Seguridad
- [ ] Credenciales en variables de entorno
- [ ] No hardcoded secrets
- [ ] Credenciales rotables

### Reliability
- [ ] Retry logic implementado
- [ ] Timeout configurado
- [ ] Circuit breaker (opcional)
- [ ] Fallback strategy

### Performance
- [ ] Caching implementado
- [ ] Rate limiting respetado
- [ ] Connection pooling

### Observability
- [ ] Logging de requests/responses
- [ ] Métricas expuestas
- [ ] Alertas configuradas

### Testing
- [ ] Unit tests con mocks
- [ ] Integration tests
- [ ] Error scenarios cubiertos
```
