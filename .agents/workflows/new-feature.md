---
description: Workflow para implementar una nueva feature completa
level: 2-3
personas: [backend-engineer, frontend-engineer, qa-engineer]
version: "3.6.0"
type: workflow
---

# New Feature Implementation Workflow

> **Tiempo estimado**: 2-8 horas | **Level**: 2-3

Este workflow guía la implementación de una feature completa de principio a fin.

## Pre-requisitos

1. Feature definida y aprobada (PRD o issue)
2. Diseño UI aprobado (si aplica)
3. Arquitectura validada (si es compleja)

---

## Fase 1: Planificación

### 1.1 Entender el Alcance

- [ ] Leer PRD/issue completo
- [ ] Identificar componentes afectados
- [ ] Listar dependencias

### 1.2 Breakdown de Tareas

```markdown
## Feature: {nombre}

### Backend
- [ ] Modelo de datos
- [ ] Migraciones
- [ ] Endpoints API
- [ ] Tests

### Frontend
- [ ] Componentes UI
- [ ] Integración API
- [ ] Estados (loading/error)
- [ ] Tests

### Otros
- [ ] Documentación
- [ ] Feature flags (si aplica)
```

### 1.3 Crear Rama

```bash
git checkout develop
git pull origin develop
git checkout -b feature/{nombre-feature}
```

---

## Fase 2: Backend

### 2.1 Modelo de Datos

```python
# models/{feature}.py
class Feature(Base):
    __tablename__ = "features"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    # ...
```

### 2.2 Migración

```bash
alembic revision -m "add_feature_table"
alembic upgrade head
```

### 2.3 Schemas

```python
# schemas/{feature}.py
class FeatureCreate(BaseModel):
    name: str

class FeatureResponse(BaseModel):
    id: str
    name: str
```

### 2.4 Servicio

```python
# services/{feature}_service.py
class FeatureService:
    async def create(self, data: FeatureCreate) -> Feature:
        ...
```

### 2.5 Endpoints

```python
# routes/{feature}.py
@router.post("/", response_model=FeatureResponse, status_code=201)
async def create_feature(data: FeatureCreate):
    return await service.create(data)
```

### 2.6 Tests Backend

```python
# tests/test_{feature}.py
async def test_create_feature(client):
    response = await client.post("/api/v1/features", json={...})
    assert response.status_code == 201
```

---

## Fase 3: Frontend

### 3.1 Tipos

```typescript
// types/{feature}.ts
interface Feature {
  id: string;
  name: string;
}
```

### 3.2 API Client

```typescript
// lib/api/{feature}.ts
export const featuresApi = {
  getAll: () => api.get<Feature[]>('/features'),
  create: (data: CreateFeatureDto) => api.post<Feature>('/features', data),
};
```

### 3.3 Custom Hook

```typescript
// hooks/use-{feature}.ts
export function useFeatures() {
  return useQuery({ queryKey: ['features'], queryFn: featuresApi.getAll });
}
```

### 3.4 Componentes

```typescript
// components/features/{feature}/
├── feature-list.tsx
├── feature-card.tsx
├── feature-form.tsx
└── index.ts
```

### 3.5 Página

```typescript
// app/(dashboard)/features/page.tsx
export default function FeaturesPage() {
  const { data: features } = useFeatures();
  return <FeatureList features={features} />;
}
```

### 3.6 Tests Frontend

```typescript
// __tests__/feature-card.test.tsx
it('renders feature name', () => {
  render(<FeatureCard feature={mockFeature} />);
  expect(screen.getByText(mockFeature.name)).toBeInTheDocument();
});
```

---

## Fase 4: Integración

### 4.1 E2E Tests

```typescript
// e2e/features.spec.ts
test('user can create feature', async ({ page }) => {
  await page.goto('/features');
  await page.click('button:has-text("New")');
  await page.fill('input[name="name"]', 'Test Feature');
  await page.click('button:has-text("Create")');
  await expect(page.locator('text=Test Feature')).toBeVisible();
});
```

### 4.2 Manual Testing

- [ ] Happy path funciona
- [ ] Edge cases manejados
- [ ] Error states funcionan
- [ ] Mobile responsive

---

## Fase 5: Finalización

### 5.1 Cleanup

- [ ] Remover console.logs
- [ ] Remover código comentado
- [ ] Verificar imports no usados

### 5.2 Documentación

- [ ] README actualizado (si aplica)
- [ ] API docs actualizados
- [ ] Changelog entry

### 5.3 Code Review

```bash
git push origin feature/{nombre}
# Crear PR
```

### 5.4 Merge

- [ ] PR aprobado
- [ ] CI pasando
- [ ] Sin conflictos
- [ ] Squash & merge

---

## Checklist Final

```markdown
## Feature: {nombre}

### Backend
- [ ] Modelo creado
- [ ] Migración aplicada
- [ ] Endpoints funcionando
- [ ] Tests pasando (>80% cov)

### Frontend
- [ ] Componentes creados
- [ ] Integración API
- [ ] Estados handling
- [ ] Tests pasando

### Quality
- [ ] Linter pasando
- [ ] E2E tests
- [ ] Manual testing
- [ ] Documentación

### Deploy
- [ ] PR aprobado
- [ ] Merged a develop
- [ ] Tested en staging
- [ ] Ready for production
```

---

## 🛠️ Herramientas Sugeridas

| Fase | Herramienta |
|------|-------------|
| Planificación | `write_to_file` (crear plan), `view_file` (revisar existente) |
| Backend | `run_command` (alembic, pytest), `grep_search` |
| Frontend | `run_command` (npm test), `browser_subagent` |
| Validación | `run_command` (pytest, ruff, eslint) |

## ⚠️ Errores Comunes

| Error | Solución |
|-------|----------|
| Empezar sin PRD aprobado | Validar requerimientos primero |
| Backend y Frontend en paralelo sin contrato | Definir API contract primero |
| Olvidar estados (loading/error/empty) | Usar checklist de estados |
| Tests solo happy path | Agregar tests de errores y edge cases |
