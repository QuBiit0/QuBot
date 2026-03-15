---
description: Workflow para testing completo de una aplicación
level: 2
personas: [qa-engineer, backend-engineer, frontend-engineer]
---

# Testing Strategy Workflow

Este workflow define la estrategia de testing para el proyecto.

## Pirámide de Tests

```
         ┌───────┐
         │  E2E  │  Pocos, lentos, costosos
        /─────────\
       /  Integration\   Algunos, moderados
      /───────────────\
     /     Unit Tests   \  Muchos, rápidos, baratos
    /─────────────────────\
```

---

## Unit Tests

### Qué testear
- Funciones de utilidad
- Lógica de negocio
- Transformaciones de datos
- Validaciones

### Python (pytest)

```python
# tests/unit/test_utils.py
import pytest
from app.utils import calculate_discount

class TestCalculateDiscount:
    def test_percentage_discount(self):
        result = calculate_discount(100, percentage=10)
        assert result == 90
    
    def test_fixed_discount(self):
        result = calculate_discount(100, fixed=15)
        assert result == 85
    
    def test_negative_result_returns_zero(self):
        result = calculate_discount(10, fixed=20)
        assert result == 0
    
    @pytest.mark.parametrize("amount,percentage,expected", [
        (100, 10, 90),
        (50, 20, 40),
        (0, 50, 0),
    ])
    def test_parametrized(self, amount, percentage, expected):
        assert calculate_discount(amount, percentage) == expected
```

### TypeScript (Jest)

```typescript
// __tests__/utils.test.ts
import { formatCurrency } from '../utils';

describe('formatCurrency', () => {
  it('formats positive numbers', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });
  
  it('handles zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });
  
  it('formats negative numbers', () => {
    expect(formatCurrency(-100)).toBe('-$100.00');
  });
});
```

---

## Integration Tests

### Qué testear
- Endpoints API
- Database queries
- Service interactions
- External API calls (mocked)

### API Tests (pytest + httpx)

```python
# tests/integration/test_users_api.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestUsersAPI:
    async def test_create_user(self, client):
        response = await client.post("/api/users", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    async def test_create_user_duplicate_email(self, client, existing_user):
        response = await client.post("/api/users", json={
            "email": existing_user.email,
            "name": "Another User"
        })
        
        assert response.status_code == 409
```

### Database Tests

```python
# tests/integration/test_user_repository.py
class TestUserRepository:
    async def test_create_and_find(self, db_session):
        repo = UserRepository(db_session)
        
        # Create
        user = await repo.create(UserCreate(email="test@example.com"))
        
        # Find
        found = await repo.get_by_email("test@example.com")
        
        assert found is not None
        assert found.id == user.id
```

---

## E2E Tests & UI Testing

> [!CAUTION]
> **STRICT RULE (Rule 05)**: Para pruebas de extremo-a-extremo visuales, es de carácter obligatorio utilizar **Playwright**. Selenium y Cypress se consideran alternativas legadas a menos que el cliente indique explícitamente lo contrario.

### Qué testear
- User flows críticos (Checkout, Login, Alta de entidades core).
- Flujos visuales de autenticación OAuth/OIDC.
- Accesibilidad de contraste y roles W3C nativamente desde Playwright.

### Playwright

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login flow', () => {
  test('successful login', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome')).toBeVisible();
  });
  
  test('invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});
```

---

## Component Tests (Frontend)

```tsx
// __tests__/UserCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from '../UserCard';

const mockUser = {
  id: '1',
  name: 'John Doe',
  email: 'john@example.com',
};

describe('UserCard', () => {
  it('renders user information', () => {
    render(<UserCard user={mockUser} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
  
  it('calls onEdit when edit button clicked', () => {
    const onEdit = jest.fn();
    render(<UserCard user={mockUser} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    
    expect(onEdit).toHaveBeenCalledWith(mockUser);
  });
});
```

---

## Code Coverage

### Objetivos

| Tipo | Cobertura Mínima |
|------|------------------|
| Unit Tests | 80% |
| Integration | Key paths |
| E2E | Critical flows |

### Comandos

```bash
# Python
pytest --cov=app --cov-report=html

# JavaScript
npm test -- --coverage
```

---

## Testing Checklist

```markdown
## Para cada PR
- [ ] Unit tests para nueva lógica
- [ ] Integration tests para nuevos endpoints
- [ ] E2E tests si es flujo crítico
- [ ] Coverage no disminuyó

## Para refactoring
- [ ] Tests existentes siguen pasando
- [ ] No cambios a tests (salvo estructura)

## Para bugs
- [ ] Test que reproduce el bug
- [ ] Fix hace pasar el test
- [ ] Regression test agregado
```

---

## Test Data

### Contract Testing (APIs Restrictas)
> [!IMPORTANT]
> **STRICT RULE (Rule 05)**: Todo microservicio u API orientada a consumo público/federado debe ser cubierta por un esquema estricto (OpenAPI/Pact). Cualquier cambio que altere el contrato JSON (Breaking Change) causará el fallo inminente del Pull Request pre-commit.

### Fixtures (pytest)

```python
# conftest.py
@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User"
    )

@pytest.fixture
async def db_user(db_session, sample_user):
    db_session.add(sample_user)
    await db_session.commit()
    return sample_user
```

### Factories

```python
# tests/factories.py
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.LazyFunction(uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
```
