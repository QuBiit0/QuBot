# Testing Strategy Reference — QA Engineer

> Framework de estrategia de testing con niveles, herramientas y patrones.

## Pirámide de Testing

```
         ╱╲
        ╱ E2E╲         ← Pocos, lentos, costosos
       ╱──────╲           Playwright, Cypress
      ╱ Integr. ╲      ← Moderados, API + DB
     ╱────────────╲       httpx, supertest
    ╱  Unit Tests   ╲   ← Muchos, rápidos, baratos
   ╱──────────────────╲   pytest, jest
```

## Distribución Recomendada

| Nivel | Cantidad | Velocidad | Costo | Coverage Target |
|-------|----------|-----------|-------|-----------------|
| Unit | 70-80% | < 1s | Bajo | 80%+ |
| Integration | 15-25% | < 10s | Medio | Flujos críticos |
| E2E | 5-10% | < 60s | Alto | Happy paths |

## Framework por Stack

### Python (pytest)

```python
# conftest.py — Fixtures estándar
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Cliente HTTP para tests de integración."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def user_factory():
    """Factory para crear usuarios de test."""
    def make_user(**kwargs):
        defaults = {
            "email": "test@example.com",
            "name": "Test User",
            "is_active": True,
        }
        defaults.update(kwargs)
        return defaults
    return make_user
```

### JavaScript/TypeScript (jest)

```typescript
// jest.config.ts
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

## Patrones de Tests Efectivos

### AAA Pattern (Arrange-Act-Assert)

```python
class TestUserService:
    async def test_create_user_with_valid_data(self, user_service, user_factory):
        # Arrange
        data = user_factory(email="new@example.com")

        # Act
        user = await user_service.create_user(data)

        # Assert
        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.is_active is True
```

### Given-When-Then (BDD Style)

```python
class TestOrderFlow:
    async def test_order_completion(self):
        """
        GIVEN un usuario con items en el carrito
        WHEN confirma el pedido
        THEN se crea una orden con estado 'pending'
        """
        # Given
        cart = await create_cart_with_items(user_id="123", items=3)

        # When
        order = await confirm_order(cart.id)

        # Then
        assert order.status == "pending"
        assert len(order.items) == 3
```

## Testing de APIs

### Test de Endpoint Completo

```python
class TestUserEndpoints:
    @pytest.mark.asyncio
    async def test_create_user(self, client):
        response = await client.post("/api/v1/users", json={
            "email": "new@test.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert "password" not in data  # No exponer password

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client, existing_user):
        response = await client.post("/api/v1/users", json={
            "email": existing_user.email,
            "password": "AnyPass123!",
        })
        assert response.status_code == 409
```

## Errores Comunes en Tests

| ❌ Error | ✅ Corrección |
|---------|-------------|
| Tests que dependen de orden de ejecución | Cada test debe ser independiente |
| Datos hardcodeados | Usar factories y fixtures |
| Tests flaky (a veces fallan) | Eliminar dependencias de tiempo/red |
| Testear implementación, no comportamiento | Testear qué hace, no cómo lo hace |
| Assertions vagas (`assert result`) | Assertions específicas (`assert result.status == "ok"`) |
| Un test que verifica 10 cosas | Un assert principal por test |
| Mock excesivo | Mockear solo boundaries (DB, APIs externas) |

## Coverage Mínimo por Tipo de Código

| Tipo | Mínimo | Ideal |
|------|--------|-------|
| Lógica de negocio (services) | 85% | 95% |
| API endpoints | 80% | 90% |
| Utilities/helpers | 90% | 100% |
| Modelos/schemas | 60% | 80% |
| Configuración | 50% | 70% |
